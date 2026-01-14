# WORLD_MANIFEST_DOCS

## Canonical (Phase1)
- Docs / Config / Scripts are fixed by **Git tag (or commit)**.
- This manifest defines the **canonical world** for handover and reproduction of docs/config.

## World ID (Tag)
- TAG format: `DOCS_WORLD_YYYY-MM-DD_nn`
- **Current Canonical TAG (MUST): `DOCS_WORLD_2026-01-15_04`**

## Scope (fixed in this world)
- `docs_all/`   (RUNBOOK / LEDGER / COMMUNICATION_RULES / LOCK files)
- `config/`     (exclusions.json, etc.)
- `scripts/`    (reference only in Phase1)

## Scripts handling (Phase1)
- `scripts/` are included as **reference artifacts**.
- Execution portability is **NOT guaranteed** in Phase1.
- Some scripts may contain **local absolute paths** (e.g. `C:\work\boatrace`).
- **Worldline safety applies to docs/config only**.
- Script path refactoring is deferred to **Phase2** (if approved).

## Rules (MUST)
- **"Latest" is forbidden.** Always refer to **TAG or commit**.
- Any change requires a **new commit** and (**recommended**) a **new TAG**.
- Proposals are welcome, but **outputs must follow canonical docs**.

## Optional: Drive usage (Phase1)
- Drive may be used for sharing **handover bundles** and **large outputs** (optional).

## Docs 正本宣言（WORLD FIX / Public）
- Canonical Docs Repository: **fishmen-create/boatrace-docs-world**
- Visibility: **Public**
- Canonical is **TAG-fixed**. Direct reference to `main/latest/HEAD` is forbidden.
