# Source map and public adaptations

The original shared engine and event operations workspace are consolidated here. These are source-derived implementations, with explicit public adaptations.

| Public files | Origin and treatment |
|---|---|
| `.claude/workflows/*.js` | Original two workflows: inline agent roles, prompts, JSON schemas, phase order, parallel fanout, filtering and results. Replaced organization-specific priority rules with inputs, made the date range configurable, added input guards, and fixed failed-response handling. |
| `.claude/skills/`, `.claude/commands/`, `.agent-skills/research.md` | Original task instructions and command wrappers. Removed personal/event-specific text, internal links and IDs; replaced local paths and organization names with generic configuration. Renamed the repository-improvement skill generically. |
| `.claude/skills/speaker-prospectus/fill_prospectus.py` | Original Google Docs automation. Replaced real examples and document identifiers, bounded placeholder searches by section, and added offline tests. |
| `.claude/scripts/journal-*`, `.claude/settings.json` | Original workspace session-memory scripts and hook structure. Removed fixed personal paths, added opt-in summarization, isolated summarizer tools/hooks, improved session-ID handling and locking, and hardened malformed transcript parsing. |
| `methodology/` | Original reusable gates, learning protocol and research prompt, sanitized. The planning framework is a new condensed description of the reusable rules, without internal examples and decision history. |
| `templates/_instance/` | Original event-folder layout and instance concept, with generic state templates and public configuration. |
| `scripts/sync-engine.sh` | Adapted source distribution mechanism: pin a source revision, copy managed assets, retain event state. Public version fetches a fresh tree, checks managed assets and destination symlinks, and records the full commit. |
| `scripts/workflow-runtime.mjs`, `scripts/run-workflow.mjs` | New public runtime adapter for the original host-style workflow files. Supplies fixture or Claude CLI agents, bounded concurrency, call limits and error reports. |
| `examples/`, `tests/`, public setup docs and publication scanner | New synthetic fixtures, offline regression tests and instructions. These are not historical event outputs. |

The separate workspace repository now points here. The earlier explanation-only demos were removed from the current tree. Private source history, actual research results, contacts, messages, journal entries, and internal documents were not imported.

There is no standalone `.claude/agents` configuration in the source projects. The agent definitions are the prompt/schema calls inside the workflows; the skill files guide the assistant that prepares their inputs and uses their results.
