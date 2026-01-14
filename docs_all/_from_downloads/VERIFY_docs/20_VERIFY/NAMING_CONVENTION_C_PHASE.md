# 命名規約（Cフェーズ）

## 目的
- Cフェーズの成果物（C_OUT / 選定結果 / 診断CSVなど）を、日付・対象・方式・世界線で一意に識別し、運用と検証を混在させない。

## 適用範囲
- Cフェーズの成果物フォルダ/ファイルに適用する。
- **骨格は CORE（正本）に従う**（WORLD必須 / WINDOW形式固定 / 任意suffixは末尾のみ）。

## フォルダ命名（骨格のみ：まず固定）
```
BR__OPS__C__<WORLD>__<WINDOW>__<VARIANT>__<STAMP>__<OPT...>/
```

### WORLD
- 通常運用（Cフェーズ実行）は `BT` を基本とする（運用再現）
- 参考比較（制約なし性能の確認など）は `BL` を使う（ただし運用採用判断はBTで）

### WINDOW（当面）
- 日次運用は同日指定：`YYYY-MM-DD_YYYY-MM-DD` で同日（例：`2026-01-13_2026-01-13`）

### 任意suffix（今後の議論で語彙を追加）
- 対象：`TRACK_ALL` / `TRACK_XX` など
- 入力セット：`INPUTSET_xxx`（K/fan/features の版を表現）
- 制約：`CAP10` / `EXCL_CORE5` など

## 例（暫定）
- 全場C（運用）
  - `BR__OPS__C__BT__2026-01-13_2026-01-13__v12__20260113_0810__TRACK_ALL__CAP10__EXCL_CORE5/`

## TODO（別タスクで確定するもの）
- Cフェーズの成果物ファイル名（report/diagnostic/c_out等）の固定
- suffix語彙（TRACK/INPUTSET/…）の確定

