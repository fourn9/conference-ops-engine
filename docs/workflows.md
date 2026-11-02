# Workflow execution

## Host API and inline agents

The two `.claude/workflows/*.js` files contain the orchestration and agent definitions. They use `args`, `agent`, `parallel`, `phase`, and `log` supplied by a host, plus top-level `return`. They are not standalone Node modules and a standard Claude Code install does not automatically supply a `Workflow` tool.

`scripts/workflow-runtime.mjs` loads only these two known, trusted files and supplies the host API. It executes their original phases, schemas, filtering and prompt construction. It provides globally bounded agent concurrency, a call limit, schema validation for the subset used here, and structured error reporting. It is not a sandbox for arbitrary workflow code.

```text
speaker-deep-research
  angles → parallel find:<angle> agents → name deduplication/exclusions
         → per-theme cap → parallel verify:<theme>:<name> agents
         → themes + searched_sources + unverified overflow (dropped)

conference-matrix
  scale → parallel A:<segment> agents → matrixA
  roles → parallel B:<role> agents    → matrixB + searched_sources
```

Research and gate verdicts are produced by the model. The runner validates response shape; it does not independently certify sources, names, gate verdicts, or dates. A speaker verdict of `確定` means a research candidate, not a confirmed booking. Review evidence before making an operational decision.

## Inputs

Speaker research requires `today`, nonempty `angles` with `theme/key/prompt`, a `gateFRules` string for each theme, and `excluded` names. `cap` defaults to 10 per theme. Optional `since`, `scopeRules`, and `priorityRules` replace organization-specific policies. Without priority rules, the prompt requests B / unassessed. Names are deduplicated globally after whitespace removal, assigned to the first theme encountered, and excluded names also use substring matching. Review ambiguous or shared names.

Matrix research requires `today`, `event`, nonempty `scale` and `roles`, and `sourceGuardA`. Optional `since` sets the Matrix B source period. Both workflows default `since` to January 1 of the supplied year.

See the JSON files in `examples/` for full inputs. Use `local/` for real inputs and results.

## Offline

Run the commands in the README. `--fixture` maps agent labels to synthetic JSON responses. It never invokes a model. A missing response, schema error, or reached call limit produces a partial report; failed rows/candidates are omitted, and `errors` explains the omission. Overflow candidates appear under `dropped`; that label means not verified due to the cap, not rejected on evidence.

Exit codes: 0 = execution completed; 2 = partial result; 1 = invalid input or fatal error. Completion does not mean all evidence gates passed.

## Live

Install and authenticate Claude Code separately. Check the installed CLI supports the flags in `claudeAgent`; the adapter was checked against local CLI help, and offline tests use a fake CLI executable. No live research, paid inference, or external account writes are part of the test suite.

```sh
mkdir -p local
cp examples/speaker-research.args.json local/research.args.json
# Replace the synthetic inputs, date, themes, exclusions, and scope first.
node scripts/run-workflow.mjs speaker-deep-research --input local/research.args.json --live --budget-usd 5 --max-calls 20 --concurrency 3 > local/research.result.json
```

`CONFERENCE_MODEL` optionally selects a model. Each agent uses `claude -p` with a JSON schema and WebSearch/WebFetch only, from a temporary working directory. MCP servers, hooks, skills, and session persistence are disabled for these calls. CLI authentication still uses your account. The runner passes the overall budget divided by the maximum call count to each invocation; limits are enforced by the CLI, not by billing reconciliation in this repository. Small per-call budgets can end a run before a result is available.

The prompt and any research inputs are sent to the configured model service. Keep real inputs and results local. [Official CLI reference](https://code.claude.com/docs/en/cli-reference)
