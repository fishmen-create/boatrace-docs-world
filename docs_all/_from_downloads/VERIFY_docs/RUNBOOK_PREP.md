# 準備パート Runbook（正本）

> 90D検証のフロー正本は `RUNBOOK_90D.md` を参照（RUNBOOK_PREP は準備パート中心）。
## ゴール
- 全場横断で長期ROI最大化（実践は1日5〜15R程度）

## 作業フォルダ
- WORK_DIR: C:\work\boatrace
- RUN_DIR : C:\work\boatrace\runs
- B_DIR   : C:\work\boatrace\b_files
- all_k   : C:\work\boatrace\all_k_results.csv（Kマージ結果の正本）

## 準備フロー（基本）
1) Bファイル準備（Downloads→b_files）
   - python .\prepare_b_files_v2.py --src "%USERPROFILE%\Downloads" --dst "C:\work\boatrace\b_files" --sevenzip "C:\Program Files\7-Zip\7z.exe"
   - python .\infer_dates_from_bfiles.py --b-dir "C:\work\boatrace\b_files" --mode plain
2) Kファイル取得（期間指定）→マージ
   - （download→mergeの流れをここに追記）
3) payout取得（最優先・resume）
   - python .\collect_boatrace_payouts_v2.py --all-k-csv "C:\work\boatrace\all_k_results.csv" --date-from YYYY-MM-DD --date-to YYYY-MM-DD --output "C:\work\boatrace\runs\payouts_all_YYYY-MM-DD_YYYY-MM-DD.csv" --resume --checkpoint-every 25
4) official features作成 → dedup
   - python .\collect_boatrace_official_features_bonly_v2.py --b-dir "C:\work\boatrace\b_files" --date-from YYYY-MM-DD --date-to YYYY-MM-DD --output "C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD.csv" --b-only
   - python .\dedup_official_features.py --input "C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD.csv" --output "C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD_dedup.csv"
5) preflight（欠損チェック）
   - python .\preflight_boatrace_inputs_v2.py --features "...\_dedup.csv" --payouts "...\payouts_all_....csv" --out-issues "C:\work\boatrace\runs\preflight_issues_....csv" --max-missing-payout-rate 0.20
6) backtest（該当スクリプトで実行）

## 注意（事故防止）

### 追加：WORLDメタ（BL/BTの誤読防止・必須）
- 90D/rolling/比較検証の出力は、必ず「どっちの世界か」を**1行メタ**で残す（CSV/summaryのどちらか、両方推奨）。
- 最低限のメタ（コピペ用）：
  - `WORLD=BL(mode=analysis)` または `WORLD=BT(mode=operation)`
  - `window=YYYY-MM-DD..YYYY-MM-DD`
  - `CAP=10`（なしなら `CAP=none`）
  - `EXCL=15:[03,06,07,08,11,12,13,14,16,18,19,20,21,23,24]`（なしなら `EXCL=none`）
  - `payouts=... / features=... / tickets=...`（source_of_truthのパス）
- これを残す目的：**結果CSVだけ見ても“世界線混在”を即検知**できるようにする。

### 追加：スモークテスト（mode混在防止・1回だけ）
- CANON（mode分離済み）スクリプトは、**analysisに運用制約を渡したら落ちる**のが正しい（混入防止）。
- 1回だけ下記を確認し、以後は「落ちる＝正常」と扱う。

（例：意図的に失敗させる）
```powershell
# analysis で daily-cap / exclude を渡す → エラーになる（正常）
python .\boatrace_backtest_v12_prune_configurable_s087_alltracks_CANON.py `
  --mode analysis --daily-cap 10 --exclude-jcd 03 `
  --date-from 2025-10-02 --date-to 2026-01-10 `
  --payouts-csv "C:\work\boatrace\runs\payouts_all_2025-10-02_2026-01-10.csv" `
  --features-csv "C:\work\boatrace\runs\official_features_all_2025-10-02_2026-01-10_dedup.csv" `
  --output-dir "C:\work\boatrace\runs\SMOKE_FAIL_EXPECTED"
```

（例：BTの正常系）
```powershell
# operation で daily-cap / exclude を渡す → 実行できる（正常）
python .\boatrace_backtest_v12_prune_configurable_s087_alltracks_CANON.py `
  --mode operation --daily-cap 10 --exclude-jcd 03,06,07,08,11,12,13,14,16,18,19,20,21,23,24 `
  --date-from 2025-10-02 --date-to 2026-01-10 `
  --payouts-csv "C:\work\boatrace\runs\payouts_all_2025-10-02_2026-01-10.csv" `
  --features-csv "C:\work\boatrace\runs\official_features_all_2025-10-02_2026-01-10_dedup.csv" `
  --output-dir "C:\work\boatrace\runs\SMOKE_OK"
```

- 目的：人間ミスでBL/BTが混ざったとき、**“データ不備に見える事故”を構造で潰す**。
- payout二重起動を避ける（ロック/skip設計が必要）
- K/Bの揃う共通期間に寄せる
- dedupは必須

## Payout運用（原則：既存再利用 / 例外：差分DLのみ）
- payoutは取得に時間がかかるため、検証・GUARD確認では **既存のMERGED_keynorm等を優先して使用**する。
- 期間拡張（例：ticketsを90dへ）でpayoutが不足する場合：
  1) 既存payoutの保有日付を確認して不足日を特定（dry-run）
  2) 不足日レンジのみ差分DL（必要時だけ実行）
  3) deltaを既存にマージしてdedupし、以後はマージ済みを正本として再利用
- 重要：GUARD確認が目的の局面では、payout差分DLは**必要になってから**（＝原則後回し）。

## 追加：固定窓ROI比較（candidate vs baseline）
目的：ticketsの生成期間（例: 90d）が伸びても、評価窓を固定して比較する（世界線ズレ防止）。

- 例（窓固定）：2025-10-08..2025-12-30
- payoutsは同一ファイルを使う（例：payouts_all_2025-10-02_2025-12-30_MERGED_keynorm.csv）
- candidate は「窓でフィルタした tickets」に対して CAP10+EXCL を適用してから ROI を計算する。

## 追加：payouts差分DL（CLI引数が必須）
payouts_diff_update.py は --existing / --date-from / --date-to / --collector / --all-k-csv / --output-dir / --merged-out が必須。
（例：既存 2025-10-02..2025-12-30 を 2026-01-05 まで延長）


### payout取得のPreflight（argparse/空出力を未然に防ぐ）
PowerShell:
```powershell
# 1) all_k の解決（最新を拾う）
$ALLK = (Get-ChildItem -Recurse -File -Filter "all_k_results*.csv" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1).FullName

if([string]::IsNullOrWhiteSpace($ALLK) -or !(Test-Path $ALLK)){
  throw "all_k_results*.csv が見つかりません。先にK取得→マージを実施してください。"
}
"ALLK=" + $ALLK

# 2) 期間が足りているか（まずはファイル名から簡易判定）
#    例: all_k_results_20260102_20260105.csv の末尾日=2026-01-05
if($ALLK -match '_(\d{8})\.csv$'){
  $end = [datetime]::ParseExact($Matches[1],'yyyyMMdd',$null)
  $need_to = Get-Date "2026-01-06"
  if($end -lt $need_to){ throw "all_k の末尾日($end)が必要日($need_to)に届いていません。all_k を延長してください。" }
}

# 3) 出力が空なら即停止（BOM+改行だけを弾く）
function Assert-NotEmptyCsv([string]$path){
  if(!(Test-Path $path)){ throw "出力が存在しません: $path" }
  if((Get-Item $path).Length -lt 100){ throw "出力が空です（0件/失敗の可能性）: $path" }
}
```

## 追加：source_of_truth（固定化）
- baseline: `C:\work\boatrace\config\baseline.json`
- exclusions（運用ON）: `C:\work\boatrace\config\exclusions.json`
- candidate（CAP10+EXCL deterministic v2）: `C:\work\boatrace\config\candidate_cap10_excl10.json`

## 90D意思決定ルール（v1.2：AI所感欄あり）

### 目的
- ユーザが「評価の解釈」を得意でなくても、**誤採用を防ぎつつ**意思決定できるようにする。
- 判断を委ねる場合、**可能な限り数値（ROI / 金額）で提示**する。

### 最低限の母数ルール（トリガー対象R）
- 原則：トリガー対象R **>= 30** で判定する
- 例外：トリガー対象R **20–29** は「条件付き判定（TEMP_GO / HOLD）」のみ許可
- トリガー対象R **< 20** は原則 **HOLD**（判断しない）
- 例外（20–29で判断してよい条件：全て必須）
  1) 差分損益（円）が十分大きい（目安：±10万円以上／90D換算）
  2) 改修が軽微（ケア枠・条件分岐のみ／モデル本体は不変更）
  3) 副作用が限定的（全体ROIが悪化していない）
  4) 暫定扱い（TEMP_GO 等）を明示する

### 出力フォーマット（ユーザに意思決定を委ねるときは必須）
以下を必ずセットで出す（**数値→判定→所感**の順で固定）：

#### (1) 何を比べた？
- baseline：<現行運用の定義（WORLD/期間/CAP/除外/正本パス）>
- candidate：<変更点は1つだけ。差分の要旨を1行>

#### (2) 差分サマリ（最重要：数値）
- ROI差：<candidate - baseline>
- 損益差（円）：<candidate - baseline>
- 全体R：<baseline/candidate 共通>
- トリガー対象R：<条件に該当したR数>
- （任意）平均投資/平均回収（円/レース）：<あれば>

#### (3) 判定（GO / HOLD / NO / TEMP_GO）
- 判定：<GO/HOLD/NO/TEMP_GO>
- 根拠：<数値差分 + 母数ルールへの適合を1〜2行で>

#### (4) AIの所感（補助判断・非拘束）
- この数値結果になった理由（構造）：<1〜3行>
- 長期ROI観点の所感（リスク/副作用）：<1〜3行>
- 誤採用リスク／過小評価リスク：<1〜2行>
- 次の一手（何を変える/何を追加で見るか）：<1行>

> 注意：AIの所感は「数値判断を補強する」目的。  
> 数値差分がNO/HOLDでも、所感でGOに“覆さない”。


### 90D検証 出力の固定ルール（必須）
- 結果表示の冒頭で **期間（Expected/Actual/判定OK/NG）** を必ず明記（期間ズレ検知）。
- 「比較」欄は **BL/BT×Baseline/Candidate 対比表** を必須化し、`CAP / 除外場（運用制約）= OFF/ON` で表現する。
- 詳細テンプレは `VERIFY_90D_TIGERBOOK.md` の「出力フォーマット正本」を参照。
