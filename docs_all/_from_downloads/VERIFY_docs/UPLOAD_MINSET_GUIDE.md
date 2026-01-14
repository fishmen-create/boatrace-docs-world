# CSVアップ（AI側で加工）用：最小アップロードセット（minset）

## 目的
ローカル環境の詰まり（ExecutionPolicy / パス差 / 依存関係 / 列名揺れ）を回避し、**最短で結果（races/tickets_long）を得る**。

## 1) core5除外＋CAP10（Cフェーズ後の整形）で必要なminset
必須（3点）
1. `runs\C_OUT_*DATE*_*_C_race_summary.csv`  
2. `runs\C_OUT_*DATE*_*_tickets_long.csv`  
3. `config\exclusions.json`

任意（必要な時だけ）
- `runs\official_features_all_*DATE*_dedup*.csv`（STランク再計算が必要な場合のみ）

## 2) どのファイルをアップすべきか迷ったら（最短）
- `runs\C_OUT_FIXED_YYYY-MM-DD\CAP10_core5_meta.json` がある場合  
  → `inputs` に元ファイルパスが全部載っているので、それに従う。

## 3) ローカル側の特定コマンド例（PowerShell）
```powershell
# 直近の C_OUT 実行ディレクトリを探す
$RUN = Get-ChildItem "C:\work\boatrace\runs" -Directory |
  Where-Object { $_.Name -like "C_OUT_*" } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$RUN.FullName

# その中の候補CSVを列挙（名前で探す）
Get-ChildItem $RUN.FullName -File | Sort-Object Name
```

## 4) AIに期待する戻り物（標準）
- `CAP10_core5_races.csv`（締切ソート等を適用する前のベース）
- `CAP10_core5_tickets_long.csv`
- `CAP10_core5_meta.json`（トレース用）
