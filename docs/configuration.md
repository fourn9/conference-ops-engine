# Configuration and storage

## Local workflow execution

The offline Node runner has no external dependencies. Live workflow execution needs the Claude Code CLI, authentication, and access to its WebSearch/WebFetch tools. See [workflows.md](workflows.md).

Skills are operating instructions for an assistant, not installed integrations. Manual-only skills preserve Claude Code’s `disable-model-invocation` setting ([official skill reference](https://code.claude.com/docs/en/skills)). Their references to Gmail, Slack, Calendar, Notion, Google Drive, Obsidian, or `gbrain` require the corresponding tools to be available in your environment. No connector server, credentials, workspace IDs, or existing organization permissions are bundled. If a tool is absent, the assistant should produce a local draft or ask for the missing source, and report the unavailable integration. It must not claim a remote action succeeded.

## Event workspace

Copy `templates/_instance/` outside this public checkout, then run its sync script. `.engine-source` names the public repository; `.engine-version` pins a release/tag or commit. After synchronization it contains the resolved commit SHA. To change versions, run `bash scripts/sync-engine.sh <tag-or-commit>` after reviewing its dry run.

Engine-managed paths replaced by sync: `.claude/skills`, `.claude/commands`, `.claude/workflows`, `.claude/scripts`, `.claude/settings.json`, `.agent-skills`, `methodology`, the two Node runner files, the profile and prospectus templates, `docs`, and `examples`. Keep custom documents under `conference/` and custom settings in `.claude/settings.local.json`. A sync overwrites edits within managed paths. The script rejects destination symlinks and fetches a fresh pinned source tree before copying. It does not copy event records back to the engine.

Use `conference/event.md` for the event name, dates, audience, organizer, delivery format, response deadlines, and template references. No real event values are supplied. Fill missing parameters from the user's instructions and event file; do not reuse placeholders as facts.

## Local state

| Path | Purpose |
|---|---|
| `conference/` | Event planning and operational records |
| `local/vault/` | Local research notes; optional Obsidian vault |
| `journal/` | Session summaries and index |
| `local/` | Inputs, connector notes, generated outputs |
| `.mcp.json`, `.claude/settings.local.json` | Personal connector and local tool settings |
| `USER.md`, `decisions-log.md`, `skills/`, `decisions/`, `.failure-inbox/`, `failure-patterns.md` | Local learning and decision state |

Create state files only when needed. The instance includes empty-state instructions for skills, decisions, and failures; it contains no previous records. Public root ignore rules exclude operational state, but ignore rules do not sanitize files already tracked. Review files before publishing changes.

Session journaling is opt-in and sends extracted dialogue to the configured model. [Setup and processing details](../journal/README.md). The hook configuration uses the documented [Claude Code hooks](https://code.claude.com/docs/en/hooks).

Google Docs automation needs your own template and authenticated Google API access. [Setup](google-docs.md). Other skills must follow the user's actual authorization for sending, sharing, and updating records.
