# Conference Ops Engine

**Reusable AI workflows for planning technical conferences, with evidence checks and human decisions built into the process.**

Built by [Shinichi Kimura (@fourn9)](https://github.com/fourn9), with AI coding assistants. [日本語](README.ja.md)

I built a shared workflow engine for conference operations: audience research, speaker discovery, outreach preparation, sponsor workflows, and post-event analysis. The key design was separating reusable procedures from each event's private working data, so improvements could be shared without merging the events' records.

This repository is a **public case study and newly written reference demo**. It explains earlier private work; its demo code was created for this public release and is not the original implementation.

## Try it in 30 seconds

Python 3.9 or newer; standard library only. No installation, account, API key, or network access required.

```bash
git clone https://github.com/fourn9/conference-ops-engine.git
cd conference-ops-engine
python3 demo/research.py
python3 -m unittest discover -s tests -v
```

The synthetic fixture produces **1 ready for review, 2 pending, and 1 rejected** candidate. These are demo outcomes, not results from a real event. [Read the sample output](examples/research-review.md).

```text
Audience interviews + topic brief
               |
      Independent research batches
               |
    Source / authorship / fit checks
               |
    Ready for review | Pending | Rejected
               |
        Event owner's decision
```

## What I built in the private project

| Area | Implementation represented in the original project |
| --- | --- |
| Reusable workflows | Task-specific skills and commands for research, communications, sponsorship, and reporting |
| Research orchestration | JavaScript workflows that fan out across topics or audience segments, then validate structured results |
| Evidence discipline | Source review, authorship checks, topic fit, explicit uncertainty, and links back to audience interviews |
| Distribution | A shared engine and event-specific repositories; a sync script imports a chosen engine version |
| Improvement loop | Local observations become candidate improvements, then reviewed changes to the shared engine |

The work is an agent-assisted workflow system built from Markdown, JavaScript, shell, and Python, rather than a hosted application. The companion [Conference Ops Workspace](https://github.com/fourn9/conference-ops-workspace) explains the event-level operations and memory layer.

## What the public demo demonstrates

[`demo/research.py`](demo/research.py) runs independent synthetic topic batches concurrently and evaluates recorded evidence. It keeps incomplete records pending, preserves conflicting duplicate records for review, and requires a recorded interview reference before a candidate can be ready for review.

All people and interviews are fictional. `example.org` links are placeholders, not research citations. The demo evaluates supplied flags; it does not browse, authenticate evidence, call an LLM, send invitations, or implement the original integrations. Human approval remains a separate step.

```bash
# Machine-readable output
python3 demo/research.py --json

# A different explicitly synthetic fixture
python3 demo/research.py path/to/synthetic-fixture.json
```

## Read more

- [Case study: problem, architecture, trade-offs, and scope](docs/case-study.md)
- [Short project description for an application](docs/application-summary.md)
- [Publication scope](PUBLICATION.md)

The case study describes capabilities visible in the reviewed source. It makes no claim about adoption, revenue, time saved, or independently measured model accuracy. The runnable demo and its tests are independently inspectable here.

## License

[MIT](LICENSE) covers the new material in this repository. It grants no rights to the private projects or their data.
