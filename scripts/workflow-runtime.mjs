import { readFile, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execute = promisify(execFile);
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const known = new Set(['speaker-deep-research', 'conference-matrix']);

// Validates the subset used by the actual workflow schemas in this repository.
export function validate(value, schema, path = '$') {
  if (schema.type === 'object') {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${path}: expected object`);
    for (const key of schema.required || []) {
      if (!(key in value)) throw new Error(`${path}.${key}: required`);
    }
    for (const [key, child] of Object.entries(schema.properties || {})) {
      if (key in value) validate(value[key], child, `${path}.${key}`);
    }
  } else if (schema.type === 'array') {
    if (!Array.isArray(value)) throw new Error(`${path}: expected array`);
    value.forEach((item, i) => validate(item, schema.items, `${path}[${i}]`));
  } else if (schema.type && typeof value !== schema.type) {
    throw new Error(`${path}: expected ${schema.type}`);
  }
}

export function fixtureAgent(responses) {
  if (responses.synthetic !== true || !responses.responses) throw new Error('Fixture must declare synthetic: true and responses');
  return async (_prompt, { label }) => {
    if (!(label in responses.responses)) throw new Error(`No fixture response for ${label}`);
    const response = responses.responses[label];
    if (response?.fixture_error) throw new Error(response.fixture_error);
    return structuredClone(response);
  };
}

export function claudeAgent({ budgetUsd, maxCalls, model = process.env.CONFERENCE_MODEL }) {
  if (!(Number.isFinite(budgetUsd) && budgetUsd > 0) || !Number.isInteger(maxCalls) || maxCalls < 1) {
    throw new Error('Live runs require a positive budget and call limit');
  }
  const perCall = budgetUsd / maxCalls;
  return async (prompt, { schema }) => {
    const cwd = await mkdtemp(join(tmpdir(), 'conference-agent-'));
    try {
      const flags = ['-p', '--output-format', 'json', '--json-schema', JSON.stringify(schema),
        '--tools', 'WebSearch,WebFetch', '--allowedTools', 'WebSearch,WebFetch',
        '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
        '--setting-sources', '', '--settings', '{"disableAllHooks":true}',
        '--disable-slash-commands', '--no-session-persistence',
        '--max-budget-usd', String(perCall)];
      if (model) flags.push('--model', model);
      flags.push('--', prompt);
      const { stdout } = await execute('claude', flags, {
        cwd, timeout: 600000, maxBuffer: 8 * 1024 * 1024,
        env: { ...process.env, CLAUDE_JOURNAL_SUMMARIZER: '1' },
      });
      const response = JSON.parse(stdout);
      if (response.is_error || response.subtype?.startsWith('error')) throw new Error('Claude reported an unsuccessful run');
      if (!response.structured_output) throw new Error('Claude did not return structured_output');
      return response.structured_output;
    } catch (error) {
      // Do not include the child-process command: it contains the full prompt.
      throw new Error(`Claude invocation failed (${error.code || error.name || 'error'}); inspect authentication, budget and CLI compatibility`);
    } finally {
      await rm(cwd, { recursive: true, force: true });
    }
  };
}

export async function runWorkflow(name, args, adapter, { concurrency = 3, maxCalls = 20 } = {}) {
  if (!known.has(name)) throw new Error('Unknown workflow');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 16) throw new Error('concurrency must be 1..16');
  if (!Number.isInteger(maxCalls) || maxCalls < 1 || maxCalls > 100) throw new Error('maxCalls must be 1..100');
  const source = await readFile(new URL(`../.claude/workflows/${name}.js`, import.meta.url), 'utf8');
  // These trusted repository files use the original host's top-level return/API.
  const body = source.replace(/^export const meta\s*=/m, 'const meta =');
  const workflow = new AsyncFunction('args', 'agent', 'parallel', 'phase', 'log', body);
  const trace = [], errors = [];
  let calls = 0, active = 0;
  const waiting = [];
  const acquire = async () => {
    if (active < concurrency) { active++; return; }
    await new Promise(resolve => waiting.push(resolve));
  };
  const release = () => { if (waiting.length) waiting.shift()(); else active--; };
  const agent = async (prompt, options) => {
    if (calls >= maxCalls) {
      errors.push({ label: options.label, error: 'Agent call limit reached' });
      return null;
    }
    calls++;
    await acquire();
    try {
      const value = await adapter(prompt, options);
      validate(value, options.schema);
      trace.push({ label: options.label, phase: options.phase, status: 'returned' });
      return value;
    } catch (error) {
      errors.push({ label: options.label, error: error.message });
      return null;
    } finally { release(); }
  };
  const result = await workflow(args, agent,
    tasks => Promise.all(tasks.map(task => task())),
    name => trace.push({ phase: name }),
    message => trace.push({ message }));
  return { workflow: name, status: errors.length ? 'partial' : 'complete', result, calls, errors, trace };
}
