# Conference Ops Engine

Workflows, agent instructions, and workspace templates for technical conference planning and operations. [日本語](README.ja.md)

This repository combines the reusable engine and event-workspace mechanisms from two operational projects. It contains sanitized source implementations: research prompts and schemas, agent orchestration, task skills, document automation, session journals, and version-pinned workspace distribution. Event records and private service configuration are excluded.

## Implementation

| Component | What it does | Source |
|---|---|---|
| Speaker research | Parallel discovery by theme/angle → deduplication and exclusions → capped per-person verification | [workflow](.claude/workflows/speaker-deep-research.js) |
| Planning matrices | Business scale × purpose research, then role × purpose research with evidence gates | [workflow](.claude/workflows/conference-matrix.js) |
| Task skills | Speaker outreach, sponsor operations, proposal documents, email, event copy, reporting, and learning | [16 skills](.claude/skills) / [commands](.claude/commands) |
| Document automation | Copy a Google Doc template; fill five anchored sections; preserve indexes and native bullets | [Python implementation](.claude/skills/speaker-prospectus/fill_prospectus.py) |
| Session memory | Extract dialogue → summarize → append journal/index → recall or search | [hook configuration](.claude/settings.json) / [scripts](.claude/scripts) |
| Event workspace | Event folder structure and selective, version-pinned engine updates | [template](templates/_instance) / [sync script](scripts/sync-engine.sh) |

Agent roles are defined **inside the workflow files**, as `agent(prompt, { label, phase, schema })` calls. There is no separate `.claude/agents` directory. The workflows preserve the original host API; a new Node.js adapter supplies that API using either fixture responses or Claude Code CLI. [Execution details](docs/workflows.md)

## Run locally

Requires Node.js 22+ for the runner; Python 3.9+, Bash, and Git for the supporting scripts. Offline examples require no packages, credentials, or model calls.

```sh
node scripts/run-workflow.mjs speaker-deep-research --input examples/speaker-research.args.json --fixture examples/speaker-research.responses.json
node scripts/run-workflow.mjs conference-matrix --input examples/matrix.args.json --fixture examples/matrix.responses.json
```

Both commands execute the actual workflow source. Responses are explicitly synthetic and test the orchestration, not research accuracy. The output includes the result, phases, agent labels, call count, and errors. Partial results exit with code 2.

For live research, configure Claude Code and provide your own inputs and explicit spending/call limits. See [workflows](docs/workflows.md). External integrations and model-driven evidence judgments have not been verified by the offline tests.

## Create an event workspace

```sh
cp -R templates/_instance ../my-conference
cd ../my-conference
bash scripts/sync-engine.sh --dry-run
bash scripts/sync-engine.sh
```

Edit `conference/event.md` and configure your own tools. The template pins the engine release; synchronization records its resolved commit. It replaces only engine-managed paths, retaining event content, local configuration, and journals. Keep event workspaces private when they contain operational records. [Configuration](docs/configuration.md)

## Verify

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check-publication.py
```

[Architecture and source adaptations](docs/source-map.md) · [Planning rules](methodology/conference-planning-framework.md) · [Session journal](journal/README.md) · [Google Docs setup](docs/google-docs.md) · [Publication scope](PUBLICATION.md)
