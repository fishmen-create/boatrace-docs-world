# 準備パート Runbook（正本）
## ゴール
- 全場横断で長期ROI最大化（実践は1日5〜15R程度）

## まず最初に：90Dの「型」を選ぶ（世界線ズレ防止）
このRunbook内で「90D」と言うとき、**どちらの型で作るかを先に固定**する。

- [ ] **C型（運用再現 / C_OUT積み上げ）**：運用の意思決定（S/A判定→除外→CAP10→買い目/金額）をそのまま再現して90D化する  
  - CAP10：⭕（運用制約として適用）  
  - 場除外：⭕（運用用除外として適用）  
  - 目的：**実運用をそのまま90日分にしてROIを見る**
- [ ] **再計算型（分析用 / S相当の性能評価）**：90D分を再計算して conf≥0.87（S相当）の集合で性能を評価する（S/Aラベルは作らない）  
  - CAP10：❌（原則適用しない）  
  - 場除外：❌（原則適用しない。入れるなら“別軸の比較”として明示）  
  - 目的：**モデル構造の性能（ROI/安定性）を見る**

> 重要：**再計算型に運用制約（CAP10・場除外）を混ぜると、性能評価と制約による件数減が混ざり、解釈不能になりやすい。**



## 作業フォルダ
- WORK_DIR: C:\work\boatrace
- RUN_DIR : C:\work\boatrace\runs
- B_DIR   : C:\work\boatrace\b_files
- all_k   : C:\work\boatrace\all_k_results.csv（Kマージ結果の正本）

## 準備フロー（基本）
1) Bファイル準備（Downloads→b_files）
   - python .\prepare_b_files_v2.py --src "%USERPROFILE%\Downloads" --dst "C:\work\boatrace\b_files" --sevenzip "C:\Program Files\7-Zip\7z.exe"
   - python .\infer_dates_from_bfiles.py --b-dir "C:\work\boatrace\b_files" --mode plain
2) Kファイル取得（期間指定）→マージ（重要：詰まりポイント対策）
   - 正本のK格納先（input-dir）は **k_filesではなく** 下記を使用する：
     - K_DIR : C:\work\boatrace\mbrace_k_results
     ※環境によって `C:\work\boatrace\k_files` が存在しない／別用途になっており、ここで毎回詰まりやすい。
   - K取得（YYYYMMDD形式）
     - python .\download_mbrace_k.py --date-from YYYYMMDD --date-to YYYYMMDD --out-dir "C:\work\boatrace\mbrace_k_results"
   - Kマージ（all_k_results.csv を正本として生成）
     - python .\merge_k_results.py --input-dir "C:\work\boatrace\mbrace_k_results" --output "C:\work\boatrace\all_k_results.csv" --date-from YYYYMMDD --date-to YYYYMMDD
   - 完了判定（空出力を即検知）
     - PowerShell:
       ```powershell
       cd C:\work\boatrace
       $k = Import-Csv .\all_k_results.csv
       if(($k | Measure-Object).Count -eq 0){ throw "all_k_results.csv が空です（K_DIRや期間を再確認）" }
       ($k | Select-Object -ExpandProperty date | Sort-Object -Unique).Count
       $k | Sort-Object date | Select-Object -First 1
       $k | Sort-Object date | Select-Object -Last 1
       ```
   - （任意）互換：古い手順が `k_files` を前提にしている場合
     - 管理者権限が無い環境では symlink は失敗しがちなので、**リンクで吸収せず**、上記の通り `--input-dir` を明示する運用を正とする。
3) payout取得（最優先・resume）
   - python .\collect_boatrace_payouts_v2.py --all-k-csv "C:\work\boatrace\all_k_results.csv" --date-from YYYY-MM-DD --date-to YYYY-MM-DD --output "C:\work\boatrace\runs\payouts_all_YYYY-MM-DD_YYYY-MM-DD.csv" --resume --checkpoint-every 25
4) official features作成 → dedup
   - python .\collect_boatrace_official_features_bonly_v2.py --b-dir "C:\work\boatrace\b_files" --date-from YYYY-MM-DD --date-to YYYY-MM-DD --output "C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD.csv" --b-only
   - python .\dedup_official_features.py --input "C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD.csv" --output "C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD_dedup.csv"
5) preflight（欠損チェック）
   - python .\preflight_boatrace_inputs_v2.py --features "...\_dedup.csv" --payouts "...\payouts_all_....csv" --out-issues "C:\work\boatrace\runs\preflight_issues_....csv" --max-missing-payout-rate 0.20
6) backtest（該当スクリプトで実行）

## 注意（事故防止）
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
