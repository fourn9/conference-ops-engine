import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, mkdtemp, writeFile, chmod, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { runWorkflow, fixtureAgent, claudeAgent } from '../scripts/workflow-runtime.mjs';

const json = async name => JSON.parse(await readFile(new URL(`../examples/${name}.json`, import.meta.url), 'utf8'));
const speaker = async () => [await json('speaker-research.args'), await json('speaker-research.responses')];

test('actual speaker workflow: fanout, exclusions, deduplication, cap and verdict preservation', async () => {
  const [args, responses] = await speaker();
  const report = await runWorkflow('speaker-deep-research', JSON.stringify(args), fixtureAgent(responses));
  assert.equal(report.status, 'complete'); assert.equal(report.calls, 4);
  assert.deepEqual(report.result.themes.migration.map(x => x.name), ['Example A', 'Example B']);
  assert.deepEqual(report.result.themes.migration.map(x => x.verdict), ['確定', '保留']);
  assert.equal(report.result.themes.migration[1].url_ok, false);
  assert.deepEqual(report.result.dropped.migration, ['Example C（Example Company）']);
  assert.equal(report.result.searched_sources.length, 2);
  assert.deepEqual(report.trace.filter(x => x.phase && !x.label).map(x => x.phase), ['Search', 'Verify']);
});

test('cap limits verification, with overflow retained', async () => {
  const [args, responses] = await speaker();
  const report = await runWorkflow('speaker-deep-research', {...args, cap: 1}, fixtureAgent(responses));
  assert.equal(report.calls, 3); assert.equal(report.result.dropped.migration.length, 2);
  await assert.rejects(runWorkflow('speaker-deep-research', {...args, cap: 0}, fixtureAgent(responses)), /cap/);
  await assert.rejects(runWorkflow('speaker-deep-research', {...args, angles: []}, fixtureAgent(responses)), /arrays/);
});

test('failed discovery/schema responses become explicit partial results', async () => {
  const [args, responses] = await speaker();
  responses.responses['find:talks'] = {fixture_error: 'synthetic discovery failure'};
  responses.responses['verify:migration:Example B'] = {name: 'invalid'};
  const report = await runWorkflow('speaker-deep-research', args, fixtureAgent(responses));
  assert.equal(report.status, 'partial'); assert.equal(report.errors.length, 2);
  assert.equal(report.result.themes.migration.length, 1);
  assert.ok(report.errors.some(x => x.error.includes('required')));
});

test('global concurrency and call ceiling apply to actual workflow agents', async () => {
  const [args, responses] = await speaker();
  let active = 0, peak = 0;
  const adapter = fixtureAgent(responses);
  const report = await runWorkflow('speaker-deep-research', args, async (...a) => {
    active++; peak = Math.max(peak, active);
    await new Promise(resolve => setTimeout(resolve, 5));
    try { return await adapter(...a); } finally { active--; }
  }, {concurrency: 1, maxCalls: 3});
  assert.equal(peak, 1); assert.equal(report.calls, 3);
  assert.equal(report.status, 'partial'); assert.match(report.errors[0].error, /limit/);
});

test('actual matrix workflow preserves six purposes and uncertain evidence', async () => {
  const args = await json('matrix.args'), responses = await json('matrix.responses');
  const report = await runWorkflow('conference-matrix', args, fixtureAgent(responses));
  assert.equal(report.status, 'complete'); assert.equal(report.calls, 2);
  assert.equal(report.result.matrixA.Startup.cells.length, 6);
  assert.equal(report.result.matrixB.SRE.cells.length, 6);
  assert.ok(report.result.matrixA.Startup.cells.every(c => c.crosscheck_needed));
  assert.ok(report.result.matrixB.SRE.cells.every(c => !c.gate_pass));
  delete responses.responses['A:Startup'];
  const partial = await runWorkflow('conference-matrix', args, fixtureAgent(responses));
  assert.equal(partial.status, 'partial'); assert.deepEqual(partial.result.matrixA, {});
  assert.equal(partial.result.matrixB.SRE.cells.length, 6);
  await assert.rejects(runWorkflow('conference-matrix', {...args, roles: []}, fixtureAgent(responses)), /arrays/);
});

test('live adapter requires budget and isolates its mocked CLI invocation', async () => {
  assert.throws(() => claudeAgent({maxCalls: 2}), /budget/);
  const dir = await mkdtemp(join(tmpdir(), 'conference-cli-test-'));
  const previousPath = process.env.PATH;
  try {
    const bin = join(dir, 'claude'), captured = join(dir, 'args.json');
    await writeFile(bin, '#!' + process.execPath + '\n' +
      `import {writeFileSync} from 'node:fs'; writeFileSync(${JSON.stringify(captured)}, JSON.stringify({args:process.argv.slice(2),cwd:process.cwd()})); console.log(JSON.stringify({structured_output:{ok:true}}));`);
    await chmod(bin, 0o755); process.env.PATH = dir + ':' + previousPath;
    const result = await claudeAgent({budgetUsd: 4, maxCalls: 8})('synthetic prompt', {schema:{type:'object'}});
    assert.deepEqual(result, {ok:true});
    const capture = JSON.parse(await readFile(captured, 'utf8'));
    const value = flag => capture.args[capture.args.indexOf(flag) + 1];
    assert.equal(value('--max-budget-usd'), '0.5');
    assert.equal(value('--tools'), 'WebSearch,WebFetch');
    assert.equal(value('--setting-sources'), '');
    assert.deepEqual(JSON.parse(value('--mcp-config')), {mcpServers:{}});
    assert.equal(JSON.parse(value('--settings')).disableAllHooks, true);
    assert.ok(capture.args.includes('--no-session-persistence'));
    assert.ok(capture.args.includes('--disable-slash-commands'));
    assert.notEqual(capture.cwd, process.cwd());
    await assert.rejects(readFile(join(capture.cwd, 'anything')), /ENOENT/);
  } finally { process.env.PATH = previousPath; await rm(dir, {recursive:true, force:true}); }
});
