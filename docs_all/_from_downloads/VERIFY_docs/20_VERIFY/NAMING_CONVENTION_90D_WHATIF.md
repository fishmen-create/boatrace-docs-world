# 命名規約（90D検証 / _whatif）

## 目的
- 90D検証（what-if）の成果物を、世界線（BL/BT）・期間・方式・制約（CAP/除外）で一意に識別し、再現可能にする。

## 適用範囲
- `_whatif/` 配下の「1実験＝1フォルダ」に適用する。

## フォルダ命名（固定）
```
BR__VERIFY__WHATIF__<WORLD>__<WINDOW>__<VARIANT>__<STAMP>__<OPT...>/
```

### 必須トークン
- `<WORLD>`：`BL` or `BT`（必須）
- `<WINDOW>`：`YYYY-MM-DD_YYYY-MM-DD`（必須）
- `<VARIANT>`：例 `v12prune_s087`（必須）
- `<STAMP>`：`YYYYMMDD_HHMM`（必須）

### 任意suffix（必要なときだけ、末尾に追加）
- `CAP10` / `CAP_NONE`
- `EXCL_CORE5` / `EXCL_EXCL10P2` / `EXCL_NONE`
- `THEME_xxx`（例：`THEME_EXCL10P2_REBUILT`）

## 例
- BL（性能評価 / 制約なし）
  - `BR__VERIFY__WHATIF__BL__2025-10-08_2025-12-30__v12prune_s087__20260113_0315__CAP_NONE__EXCL_NONE/`
- BT（運用再現 / CAP10 + core5）
  - `BR__VERIFY__WHATIF__BT__2025-10-08_2025-12-30__v12prune_s087__20260113_0330__CAP10__EXCL_CORE5/`

## 必須成果物（この3点が揃わないものは無効）
- `MANIFEST.json`（入力・世界線・制約・コマンドの証拠）
- `roi_overall.csv`（全体ROI/invest/return）
- `roi_bytrack.csv`（場別ROI/invest/return）

## MANIFEST.json 最小要件（固定）
- `world`：BL/BT（フォルダ名と一致）
- `window.from` / `window.to`：WINDOWと一致
- `variant`：VARIANTと一致
- `constraints.daily_cap` / `constraints.exclude_jcd`
  - BL：**必ず null**
  - BT：使うなら値を入れる（空でも「none」を明示）
- `inputs`：payouts/official_features/fan/all_k_results のパス（source of truth）
- `command`：実行コマンド1行（再現用）

## 無効判定（混在事故防止）
- フォルダ名が BL なのに MANIFEST で CAP/除外が有効 → 無効
- フォルダ名が BT なのに MANIFEST に制約が書かれていない → 無効（証拠不足）


## OPT（任意suffix）語彙（90D / WHATIF 用：固定）

### CAP（daily cap）
- `CAP10`：1日上限10R（運用制約あり）
- `CAP_NONE`：daily cap なし（制約なし）

### EXCL（除外場）
- `EXCL_CORE5`：運用ONの core5（15場）除外（source_of_truth: exclusions.json）
- `EXCL_EXCL10P2`：EXCL10P2（候補/what-if）除外
- `EXCL_NONE`：除外なし

### THEME（検証テーマ）
- 形式：`THEME_<短い識別子>`（英数と`-`のみ推奨、空白なし）
- 例：`THEME_REBUILT` / `THEME_ROLLING30D` / `THEME_TRACKFILTER` など

### OPT の推奨並び（末尾のみ・順序は推奨）
- `...__CAP*__EXCL*__THEME_*`
  - 理由：制約→除外→テーマ の順が、人間にも集計にも読みやすい


## フォルダ内ファイル命名（90D / WHATIF：固定）

### 必須ファイル（この4点が揃わない what-if は無効）
- `MANIFEST.json`
  - 世界線（WORLD）、期間（WINDOW）、方式（VARIANT）、制約（CAP/EXCL）、入力（payouts/features/fan/K）、実行コマンドを記録
- `roi_overall.csv`
  - 列例：`invest, return, roi, bets, days`
- `roi_bytrack.csv`
  - 列例：`jcd, track, invest, return, roi, bets`
- `command.txt`
  - 実行コマンドを**1行**で記載（再現用）

### 条件付き必須（WORLD=BT の場合）
- `tickets_long.csv`
  - 運用再現・点検用。BTでは原則出力する。

### 任意
- `summary.txt`
  - 重要数値（ROI/件数/注意点）を数行で要約
- `diagnostic.csv`
  - 検証補助用（任意）

### 禁則（自動検知のためのルール）
- ファイル名の大小文字は固定（上記表記に一致させる）
- `roi_overall.csv` / `roi_bytrack.csv` の欠損は **即無効**
- `MANIFEST.json` の `world` がフォルダ名の WORLD と不一致 → **無効**
- `WORLD=BL` で `tickets_long.csv` が存在しても可（ただし制約は null であること）

