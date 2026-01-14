# 命名規約（CORE / 正本）

## 目的
- 生成物を「見ただけで」世界線・期間・方式が分かるようにし、**BL/BT混在事故**を防ぐ。
- 命名を機械的にパースできる形にして、集計/比較/引継ぎの保守性を上げる。

## 適用範囲
- ボートレース分析プロジェクト（BR）の成果物フォルダ/ファイル命名に適用する。
- まずは 90D検証（_whatif/）で運用し、Cフェーズにも同じ骨格を適用する。

## 共通ルール（固定）
- 区切り文字：`__`（ダブルアンダースコア）固定
- トークン順序（骨格）：次の順序を固定し、**途中に挿入しない**
  1. PROJECT
  2. DOMAIN
  3. STAGE
  4. WORLD  ← **必須**
  5. WINDOW
  6. VARIANT
  7. STAMP
  8. OPT...（任意suffix：0個以上。付けるなら末尾のみ）

## 各トークン定義（固定）
- PROJECT：`BR`
- DOMAIN：
  - `VERIFY`（検証/評価）
  - `OPS`（運用）
- STAGE：
  - `WHATIF`（検証の比較実験）
  - `C`（Cフェーズ）
  - `D`（Dフェーズ）
- WORLD：**必須**
  - `BL`（analysis / 再計算型：性能評価、制約なし）
  - `BT`（operation / C型：運用再現、CAP/除外あり得る）
- WINDOW：`YYYY-MM-DD_YYYY-MM-DD`（日付混在事故防止のためこの形式に固定）
- VARIANT：方式ID（例：`v12prune_s087`）。方式差・閾値差が残るため必須。
- STAMP：`YYYYMMDD_HHMM`（生成タイムスタンプ）
- OPT...：任意suffix（例：`CAP10` / `EXCL_CORE5` / `THEME_REBUILT`）
  - ルール：**末尾に追加のみ**（順序は自由。ただし増やすときは末尾に足す）

## 禁則（混在事故防止）
- WORLD（BL/BT）が無い成果物は無効（比較・採用判断に使わない）
- フォルダ名と内容（例：BLなのにCAP/除外が入っている）が矛盾した成果物は無効
- WINDOWの表記ゆれ（YYYYMMDD等）は禁止（必ず `YYYY-MM-DD_YYYY-MM-DD`）


## 追加固定（2026-01-13 / 検証チャット7）
- WORLD（BL/BT）は必須。
- WINDOW は `YYYY-MM-DD_YYYY-MM-DD` に固定（YYYYMMDDは禁止）。
- VARIANT は必須（方式差・閾値差が残るため）。
- OPT（任意suffix）は **末尾追加のみ**。90D/WHATIFでは `CAP* → EXCL* → THEME_*` の順を推奨。

