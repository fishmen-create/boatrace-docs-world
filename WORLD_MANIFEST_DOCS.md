# WORLD\_MANIFEST\_DOCS

## Canonical (Phase1)

* Docs/Config/Scripts are fixed by Git tag (or commit).
* This manifest defines the canonical world for handover and reproduction of docs/config.

## World ID (Tag)

* TAG: DOCS\_WORLD\_YYYY-MM-DD

## Scope (fixed in this world)

* docs\_all/   (RUNBOOK / LEDGER / COMMUNICATION\_RULES / LOCK files)
* config/     (exclusions.json etc.)
* scripts/    (reference only in phase1)

## Scripts handling (phase1)

* scripts/ are included as reference artifacts.
* Execution portability is NOT guaranteed in phase1.
* Some scripts may contain local absolute paths (e.g. C:\\work\\boatrace).
* Worldline safety applies to docs/config only.
* Script path refactoring is deferred to phase2 (if approved).

## Rules

* "Latest" is forbidden. Always refer to TAG or commit.
* Any change requires a new commit and (recommended) a new tag.
* Proposals are welcome, but outputs must follow canonical docs.

## Optional: Drive usage

* Drive is used for sharing handover bundles and large outputs (optional in phase1).

  ---
* 
* \# Docs 正本宣言（WORLD FIX / Public）
* 
* \## 正本リポジトリ（Docs）
* \- GitHub: fishmen-create/boatrace-docs-world
* \- Visibility: Public
* \- Purpose: ルール・方針・Runbook・台帳など「Docs正本」の単一ソース
* 
* \## 正本の指定方法（世界線固定）
* \- 正本は \*\*Git Tag\*\* により固定する
* \- \*\*Latest / main / HEAD の推測参照は禁止\*\*
* \- チャット・運用・検証は、必ず \*\*指定TAG\*\* を前提にする
* 
* \## 現在の正本TAG
* \- DOCS\_WORLD\_2026-01-15\_03
* 
* \## 取り込み規約
* \- Downloads 由来の文書は `docs\_all/\_from\_downloads/` に格納する
* 
* \## 更新ルール（正本更新の定義）
* \- Docs正本の更新は「commit」だけでは未確定
* \- \*\*新しいTAGを付与し、GitHubへ push された時点\*\*でのみ正本更新とみなす
* 
