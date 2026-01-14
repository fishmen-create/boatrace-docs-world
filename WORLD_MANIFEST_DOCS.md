# WORLD_MANIFEST_DOCS

## Canonical (Phase1)
- Docs/Config/Scripts are fixed by Git tag (or commit).
- This manifest defines the canonical world for handover and reproduction of docs/config.

## World ID (Tag)
- TAG: DOCS_WORLD_YYYY-MM-DD

## Scope (fixed in this world)
- docs_all/   (RUNBOOK / LEDGER / COMMUNICATION_RULES / LOCK files)
- config/     (exclusions.json etc.)
- scripts/    (reference only in phase1)

## Scripts handling (phase1)
- scripts/ are included as reference artifacts.
- Execution portability is NOT guaranteed in phase1.
- Some scripts may contain local absolute paths (e.g. C:\work\boatrace\).
- Worldline safety applies to docs/config only.
- Script path refactoring is deferred to phase2 (if approved).

## Rules
- "Latest" is forbidden. Always refer to TAG or commit.
- Any change requires a new commit and (recommended) a new tag.
- Proposals are welcome, but outputs must follow canonical docs.

## Optional: Drive usage
- Drive is used for sharing handover bundles and large outputs (optional in phase1).
