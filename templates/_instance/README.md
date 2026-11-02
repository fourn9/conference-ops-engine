# Event workspace

Copy this directory outside the engine repository. Run `bash scripts/sync-engine.sh --dry-run`, review the managed paths, then run `bash scripts/sync-engine.sh`. Edit `conference/event.md` before using the skills. `.engine-version` pins the engine release and is updated to its resolved commit after sync.

Keep this workspace private when adding real operational data. Local credentials, notes and generated journals are ignored. Event plans are intentionally trackable in this private workspace. Setup details are in `docs/configuration.md` after synchronization.
