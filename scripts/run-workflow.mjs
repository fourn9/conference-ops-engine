#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { parseArgs } from 'node:util';
import { runWorkflow, fixtureAgent, claudeAgent } from './workflow-runtime.mjs';

try {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    input: { type: 'string' }, fixture: { type: 'string' }, live: { type: 'boolean' },
    'budget-usd': { type: 'string' }, 'max-calls': { type: 'string', default: '20' },
    concurrency: { type: 'string', default: '3' },
  }});
  if (positionals.length !== 1 || !values.input || Boolean(values.fixture) === Boolean(values.live)) {
    throw new Error('Usage: node scripts/run-workflow.mjs <workflow> --input args.json (--fixture responses.json | --live --budget-usd N)');
  }
  const args = JSON.parse(await readFile(values.input, 'utf8'));
  const maxCalls = Number(values['max-calls']);
  const adapter = values.live
    ? claudeAgent({ budgetUsd: Number(values['budget-usd']), maxCalls })
    : fixtureAgent(JSON.parse(await readFile(values.fixture, 'utf8')));
  const report = await runWorkflow(positionals[0], args, adapter, {
    maxCalls, concurrency: Number(values.concurrency),
  });
  console.log(JSON.stringify({ mode: values.live ? 'live' : 'fixture', ...report }, null, 2));
  if (report.errors.length) process.exitCode = 2;
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
