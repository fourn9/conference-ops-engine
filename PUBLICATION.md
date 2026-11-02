# Publication scope

This release contains sanitized operational source and reusable templates. The shared engine and event-workspace layer are maintained here together.

Included: workflow code, inline agent prompts and schemas, task instructions, journal hook/scripts, document-filling code, generic methodology, workspace scaffolding, and version-pinned distribution.

Excluded: actual speaker/sponsor/participant records, correspondence, survey responses, internal decisions and journal entries, transcripts, private URLs and document IDs, local account paths, credentials, and service-specific connection configuration. Event-specific facts and examples were removed or replaced with explicit placeholders. Private repository histories were not imported.

The original explanation-only examples have been replaced by tests and fixtures that execute the source workflows. `examples/` contains explicitly synthetic data. Newly added runtime adapters and source adaptations are described in [source-map.md](docs/source-map.md).

`python3 scripts/check-publication.py` checks candidate public files for common credential and identifier patterns. It is a review aid, not a guarantee of anonymization; human review is still necessary before adding operational material. Generated records belong in ignored local paths or a separate private event workspace.
