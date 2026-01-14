
## 補足（表示まわり：C-5）
- **UIテーブル表示がユーザ側で見えないことがある**  
  → **必ずチャット本文にテキスト表を貼る**（CSV出力も併記）
- 正フォーマット：`締切(JST) | 場R | ランク(S/A) | ランキング | conf`
- 正ファイル名：`C_selected_races_deadline_sorted_YYYY-MM-DD_with_tier.csv`

# コマンドエラー集（boatrace運用：CAP10 / EXCL / TRUE90）

目的：エラー→調査→再実行の往復を減らすため、**「まずここ」**を固定します。  
（このファイルは “運用の心理的負担を下げる” ための手順書です）

---

## 0. まず確認する3点（90%ここ）

### A) パスが存在するか？
PowerShell:
```powershell
$paths = @(
  "C:\work\boatrace\runs\backtest_alltracks_2025-10-08_2026-01-05_v12prune_s087_tickets_long.csv",
  "C:\work\boatrace\runs\backtest_alltracks_2025-10-08_2026-01-05_v12prune_s087_report.csv",
  "C:\work\boatrace\runs\payouts_all_2025-10-02_2026-01-05_MERGED_keynorm.csv",
  "C:\work\boatrace\config\exclusions.json"
)
$paths | % { "{0} exists={1}" -f $_, (Test-Path $_) }
```

### B) `--out-prefix` を忘れてないか？
ROI計算（calc_roi_from_*）は `--out-prefix` 必須。

### C) PowerShellで `--tickets` などの行を“単体”で打ってないか？
PowerShellは `--tickets` だけ打つと構文エラーになります。  
必ず **`python ... --tickets ... --out ...` を1行**で実行。

---

## 1. よくあるエラーと対処

### (1) `required columns missing in tickets: ['tier_conf']`
**原因**：tickets_long.csv には tier_conf が入っていない（仕様）。  
**対処**：report.csv から conf をJOINして選定する（`cap10_select_conf_top10_v2.py` を使う）。

### (2) `JSONDecodeError: Unexpected UTF-8 BOM`
**原因**：exclusions.json が BOM付き。  
**対処**：スクリプト側で `utf-8-sig` で読む（対応済み）。

### (3) `Import-Csv : 引数が null または空です`
**原因**：`Get-ChildItem` が0件（ファイル作成に失敗）なのに FullName を取りに行ってる。  
**対処**：`if($null -eq $x){ throw ... }` のガードを先に入れる or **作成ログを確認**。

---



### (4) `collect_boatrace_payouts_v2.py: error: argument --all-k-csv: expected one argument`
**原因**：`--all-k-csv` に渡している変数が空（例：`$ALLK` が `$null`）。  
（PowerShellで `$ALLK` が空だと `--all-k-csv` の直後が次引数になって argparse が落ちる）

**対処（再発防止）**：実行前に「存在チェック＋表示」を必ず入れる。
```powershell
$ALLK = (Get-ChildItem -Recurse -File -Filter "all_k_results*.csv" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1).FullName

if([string]::IsNullOrWhiteSpace($ALLK) -or !(Test-Path $ALLK)){
  throw "all_k_results*.csv が見つかりません。all_k を作ってから再実行してください。"
}
"ALLK=" + $ALLK
```

---

### (5) `payouts_all_YYYY-MM-DD_YYYY-MM-DD.csv` が空（BOM+改行のみ / 0バイトに近い）
**原因**：対象日のレースを取得できていない（0件） or `--all-k-csv` の期間が対象日に届いていない。  
例：`all_k_results_..._20260105.csv` を指定して `2026-01-06` を取りに行く。

**対処**：
1) `--all-k-csv` を対象日まで含む all_k に更新（例：末尾日が 2026-01-07 など）  
2) 再実行後、**空判定ガード**で止める
```powershell
$OUT = ".\runs\payouts_all_2026-01-06_2026-01-06.csv"
if((Get-Item $OUT).Length -lt 100){
  throw "payout出力が空です（all_k期間や取得失敗を確認）"
}
```

---
### (4) `Join-Path : 引数が空の文字列であるため、パラメーター ‘Path’ にバインドできません`
**原因**：スクリプト側で `Join-Path $WorkDir ...` を呼ぶ時に、`$WorkDir` が空になっている。
（例：`$PSScriptRoot` が取れない呼び出し方／サンプルコマンドをそのまま貼って `-WorkDir ""` になっている／作業ディレクトリが想定外など）
**対処（最短）**：明示的に WorkDir を渡して実行する。
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\work\boatrace\scripts\run_C_out_core5_cap10.ps1 -Date 2026-01-02 -WorkDir C:\work\boatrace
```
**恒久対処**：`run_C_out_core5_cap10.ps1` を WorkDir 自動推定の強い版に差し替える（v2パッチ）。

## 2. 迷ったらこれ（最短）

この1本で “conf TOP10” を回して ROI まで出します：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\work\boatrace\run_cap10_conf_top10_v2.ps1 -K 10
```

conf列を指定したい場合（report.csvに tier_conf がある時）：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\work\boatrace\run_cap10_conf_top10_v2.ps1 -K 10 -ConfCol tier_conf
```

---

## 3. 追加（2026-01-08）

### 3-1) Expand-Archive : パス 'C:\Users\<あなた>\Downloads\xxx.zip' が存在しない

**原因**：手順のサンプルにある `<あなた>` をそのままコピペしている（実在しないパス）。

**対処（コピペ用）**：
```powershell
cd C:\work\boatrace
$zip = Join-Path $env:USERPROFILE "Downloads\boatrace_scripts_tools_PATCHED_HITLOSS6040_v3.zip"
Test-Path $zip
Expand-Archive -Force -Path $zip -DestinationPath C:\work\boatrace
```

---

### 3-2) run_C_out_core5_cap10.ps1 : races csv not found under C（or RunDir が "C" になる）

**症状例**：
- `races csv not found under C`
- `races csv not found under C:\work\boatrace\runs\...` ではなく **drive文字だけ** が出る

**原因**：RunDir / WorkDir の解決が弱い版（v2）で、`RunDir = "C"` のように壊れている。

**対処**：
1) `boatrace_scripts_tools_PATCHED_HITLOSS6040_v3.zip` を展開して **v3版**へ差し替え  
2) それでも迷ったら RunDir を明示：
```powershell
C:\work\boatrace\scripts\run_C_out_core5_cap10.ps1 -Date 2026-01-02 -WorkDir C:\work\boatrace -RunDir C:\work\boatrace\runs
```

**補助**：入力ファイルが run 配下にあるか確認（CAP10の races/tickets_long）
```powershell
$run = "C:\work\boatrace\runs\C_OUT_FIXED_2026-01-02"
dir $run "*CAP10*races*.csv"
dir $run "*CAP10*tickets_long*.csv"
```

---

### 3-4) Run dir not found: ...\C_OUT_FIXED_YYYY-MM-DD\C_OUT_FIXED_YYYY-MM-DD（RunDir を “日付フォルダ” で渡してしまった）

**症状例**：
- `Run dir not found: C:\work\boatrace\runs\C_OUT_FIXED_2026-01-02\C_OUT_FIXED_2026-01-02`

**原因**：
- `-RunDir` は **runs フォルダ（親）** を渡す想定。  
  ここに `...\runs\C_OUT_FIXED_YYYY-MM-DD` を渡すと、スクリプト側でさらに `C_OUT_FIXED_YYYY-MM-DD` を Join してしまい二重になります。

**対処（推奨）**：
```powershell
$D = "2026-01-02"
$RUNS = "C:\work\boatrace\runs"  # ← 親だけを渡す
$FEATURES = "C:\work\boatrace\runs\official_features_alltracks_2026-01-02_2026-01-04_dedup.csv"

powershell -NoProfile -ExecutionPolicy Bypass -File C:\work\boatrace\scripts\run_C_out_core5_cap10.ps1 `
  -Date $D -WorkDir C:\work\boatrace -RunDir $RUNS -FeaturesCsv $FEATURES
```

**チェック**：
```powershell
dir "C:\work\boatrace\runs\C_OUT_FIXED_$D" "*CAP10*races*.csv"
dir "C:\work\boatrace\runs\C_OUT_FIXED_$D" "*CAP10*tickets_long*.csv"
```

---

### 3-3) PSSecurityException : 「このシステムではスクリプトの実行が無効」

**症状例**：
- `& : このシステムではスクリプトの実行が無効になっているため、...ps1 を読み込むことができません。`

**原因**：PowerShell の ExecutionPolicy が `Restricted` / `AllSigned` などで、ps1 実行がブロックされている。

**対処（おすすめ：その場だけ・安全）**：
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Unblock-File -Path C:\work\boatrace\scripts\run_C_out_core5_cap10.ps1 -ErrorAction SilentlyContinue

# 以降は通常どおり実行
& C:\work\boatrace\scripts\run_C_out_core5_cap10.ps1 -Date 2026-01-02 -WorkDir C:\work\boatrace
```

**対処（1回だけ実行したい）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\work\boatrace\scripts\run_C_out_core5_cap10.ps1 -Date 2026-01-02 -WorkDir C:\work\boatrace
```

**補足**：会社PC等でポリシーが強制されている場合、`Set-ExecutionPolicy` が失敗することがある。その場合は「ps1を使わず python を直叩き」する（`scripts\run_C_out_core5_cap10.ps1` の中身にある python コマンドをそのまま実行）で回避可能。
### 3-3) make_core5_cap10_tickets.py: race_summary missing columns: ['track_name']

**症状（例）**
- `ValueError: [FATAL] race_summary missing columns: ['track_name']`
- `python failed: 1`（呼び出し側の ps1 で拾われる）

**原因**
- 入力の `CAP10_core5_races.csv`（= race_summary）に `track_name` 列が無い（`jcd` / `track_norm` しか無い）ケースがある。
- 旧版の `make_core5_cap10_tickets.py` は `track_name` を必須としていたため落ちる。

**対処（推奨）**
- `make_core5_cap10_tickets.py` を **v6以降**へ更新（`track_name` が無い場合、`jcd/track_norm` から自動補完）。
  - これにより `CAP10_core5_races.csv` のスキーマ揺れでも落ちにくくなる（conf等のスコアは変更しない）。

**暫定回避（どうしても今だけ）**
- `CAP10_core5_races.csv` に `track_name` を付与してから実行（`jcd→場名` のマッピングで追加）。

---

## 追加エラー（2026-01-07〜01-08）

### PowerShell で `cd /d` を使って失敗する
**症状**
- `Set-Location : 引数 'C:\work\boatrace' を受け入れる位置指定パラメーターが見つかりません。`
- 例：`cd /d C:\work\boatrace`

**原因**
- `/d` は **cmd.exe の cd** オプション。PowerShell の `cd`（=Set-Location）には存在しない。

**対処**
- PowerShellではこれだけでOK：
  - `cd C:\work\boatrace`
  - `Set-Location "C:\work\boatrace"`

---

### ps1 実行がブロックされる（ExecutionPolicy）
**症状**
- `このシステムではスクリプトの実行が無効になっているため ... PSSecurityException`

**対処（推奨順）**
1) その場だけ回避（プロセス限定）：
   - `powershell -ExecutionPolicy Bypass -File .\scripts\run_xxx.ps1 ...`
2) 恒久設定（許容できる場合のみ）：
   - `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

※社用PC等で変更できない場合は「🟡CSVアップ→AI側で加工」に切替。

---

### `Expand-Archive` の Path が null / 空
**症状**
- `Expand-Archive : パラメーター 'Path' の引数を確認できません。引数が null または空です。`

**原因**
- `$zip` 変数が未セット/空のまま。

**対処**
- まず ZIP の実在パスを特定してから実行：
  - `Get-ChildItem $HOME\Downloads -Filter "*boatrace*zip" | Sort LastWriteTime -Desc | Select -First 1`
  - `Test-Path $zip`

---

### `Copy-Item` で “自分自身を上書き” して失敗する
**症状**
- `Copy-Item : 項目 ... をそれ自体で上書きすることはできません。`

**対処**
- 退避先を別名にする（`.bak` 等）か、コピー不要（同一パスなら無意味）。

---

## C（Check準備）でよく出るエラー（C-2/C-4）

### 1) official_features collector が `--b-dir` 必須と言う
例：
`collect_boatrace_official_features_bonly_v2.py: error: the following arguments are required: --b-dir`

**原因**：Bファイル格納先を渡していない（またはBファイルが未整備）。

**対処（最小）**：
- まずBを整備：`python .\prepare_b_files_v2.py --src "$env:USERPROFILE\Downloads" --dst "C:\work\boatrace\b_files"`
- collector を `--b-dir "C:\work\boatrace\b_files"` 付きで実行

参照：`docs/C_CHECK_TIGERBOOK.md` 付録A

### 2) argparse の `expected one argument`（ALLKなどが空）
例：
`collect_boatrace_payouts_v2.py: error: argument --all-k-csv: expected one argument`

**原因**：変数（例：$ALLK）が空のまま実行している／引用符なしで崩れている。

**対処（最小）**：
```powershell
$ALLK=(dir C:\work\boatrace\all_k_results*.csv | sort LastWriteTime -Desc | select -First 1).FullName
"ALLK=" + $ALLK
```

### 3) selector が `columns overlap but no suffix specified` で落ちる
例：
`ValueError: columns overlap but no suffix specified: Index(['date', 'jcd', 'race_no'], dtype='object')`

**原因**：pandas merge/join 時に左右両方に `date/jcd/race_no` があり、suffix指定が無い実装バグ。

**対処（最小）**：
- `cap10_select_conf_top10_v3.py` がパッチ済みであることを確認（右側から `date/jcd/race_no` をdropしてjoin）。
- もしくは一時回避：右側（report側）から同名列を落としてからjoin（パッチ適用の考え方）。

### 4) `conf column not found`（fallback salvage 失敗）
**原因**：`tickets_long` に `conf` が無い（仕様）。

**対処（最小）**：
- `report.csv` の `conf` を `date|jcd|race_no` で `tickets_long` に付与して `C_tickets_long_with_conf.csv` を作る → selector

参照：`docs/C_CHECK_TIGERBOOK.md` 5章（C-4）

### 5) `run_*.ps1` の usage 文字列をそのまま打って PowerShell が `<` で落ちる
**原因**：`run_C_out.ps1 [[-Date] <string>] ...` は **ヘルプ表示**であって実行コマンドではない。

**対処（最小）**：
```powershell
Get-Help .\scripts\run_C_out.ps1 -Detailed
```