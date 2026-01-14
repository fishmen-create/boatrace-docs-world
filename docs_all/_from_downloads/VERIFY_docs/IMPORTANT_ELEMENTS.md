# 重要要素（未採用でも引継ぎ必須） 正本

## 入口（迷子防止）
- 文書索引: `DOC_INDEX.md`
- C（Check準備）の正本: `C_CHECK_TIGERBOOK.md`


## 目的
- 「まだ本採用ではないが、採用判断/運用結果に直結する重要要素」がチャット切替で漏れるのを防ぐ。
- **重要要素は必ず docs に残し、HANDOVER に必ず載せる**（未採用のままでもOK）。

## 重要要素の定義（固定）
「まだ本採用じゃないけど、採用判断に直結する」もの。例：
- 除外場/除外条件（TOP10CAPでROI>1に効く等）
- CAP/TOP10/日次上限などの制約（本数要件 5〜15R/日）と根拠
- データ取得制約（B/K/payout/features の日付ズレ、期間寄せルール）
- 欠損の扱い（列欠損時0扱い、落ちない等の安全設計）
- 二重起動防止（特に payout）
- 例外ルール（場別A- など）と適用範囲

## 置き場所（固定）
- 説明書（人間用）：`C:\work\boatrace\docs\*.md`
- 設定（機械用・任意）：`C:\work\boatrace\config\*.json`

推奨ペア（例）：
## [ADOPTED] HIT_LOSS配分（Aのみ・ST条件・60/40）
- 目的：HIT_LOSS（3連単取りこぼし局面）で、Aランクのリスクを安全枠へ寄せる。
- 条件：A かつ (axis1_st_rank>=3 or axis2_st_rank>=3)。
- 配分：3T:60% / 3F:40%（総額は維持）。
- 正本：docs/SPEC_FIXED.md（固定仕様）。
- 実装：自動反映は「あとでやること」へ（手動でも運用可）。

- docs/TRACK_EXCLUSIONS.md  + config/exclusions.json
- docs/IMPORTANT_ELEMENTS.md + config/*.json（必要に応じて）

## HANDOVER に必ず含めるファイル（最小セット）
- SPEC_FIXED.md
- RUNBOOK_PREP.md
- RUNBOOK_PRACTICE.md
- COMMUNICATION_RULES.md
- USER_TENDENCIES.md
- LEDGER.md
- TRACK_EXCLUSIONS.md
- IMPORTANT_ELEMENTS.md

## 運用ルール（AI側）
- 重要要素が発生したら、**必ず「どの正本に追記するか」を提案**し、更新版を返す。
- 検証/結果提示では、重要要素の条件（例：exclude_jcd、CAP設定、期間寄せ）を必ず明記する（空でもnone）。
- 本採用/暫定ON/OFF（what-if）のステータスを明確にし、台帳（LEDGER）で管理する。

## 変更履歴
- 2026-01-05: 初版

## 重要要素（追加）: 引継ぎの再発防止（HANDOVERガード化）

### 目的
チャット切替で「世界線（前提）」がズレて ROI が増減して見える／手順が巻き戻る、を防ぐ。

### 重要要素（固定）
- **1コマンドで HANDOVER.md + zip を生成する仕組み**（generate_handover_bundle.*）
- **HANDOVER.md は docs正本からのみ生成**し、ターミナル出力を貼らない（ログ混入経路を遮断）
- **lint（混入チェック）必須**：usage/Traceback/PSプロンプト等が含まれたら失敗
- **worldline guard の結果を必ず同梱**（tickets/payoutsの鍵一致、期間、CAP、除外、投資列、active条件）

### 運用（固定）
- 切替直前に bundle を作成し、**新チャット冒頭で HANDOVER.md + zip を投入**する。
- “今どの世界線か” は、毎回（空でも）明記して固定する。

## Payout運用（差分DL・既存再利用）【重要】
- payout取得は非常に重い（例：60日で約24時間）ため、**原則「既存payout CSVを再利用」**する。
- 新規にpayoutを取りに行く場合も、**既存からの差分（日付レンジの不足分のみ）**を取得する（フルレンジ再DLは原則しない）。
- 実装の考え方：
  - まず既存payoutの「保有日付」を確認し、不足日だけを範囲化（連続レンジ）して取得する。
  - 取得したdeltaを既存にマージし、重複はrace_key等でdedupする。
- 運用スイッチ例（BAT側）：デフォルトはDLしない（reuse only）。必要時だけ `PAYOUT_DIFF_EXECUTE=1` で差分DLを許可。

## Baseline/Candidate の “ロック” ルール（世界線固定）【重要】
- **Baseline（固定の比較基準）**
  - source_of_truth: `C:\work\boatrace\config\baseline.json`
  - 代表（直近確定ベースライン例）: tickets=`CAP10_EXCL_20251203_1230_tickets_long_racelevel_DROP_SKIP_NO_S3F.csv` / payouts=`payouts_all_2025-10-02_2025-12-30_MERGED_keynorm.csv` / ROI=0.917963
- **Candidate（実践運用）**
  - source_of_truth: `C:\work\boatrace\config\candidate_cap10_excl10.json`
  - 生成/再現コマンド: `run_candidate_cap10_excl10.ps1`（CAP10+EXCL / deterministic v2）
- 比較は必ず「同一窓・同一payouts・key_overlap_rate=1.0000」を満たすこと。

## 除外場の本採用（Core5 / 2026-01-06）【重要】
- source_of_truth: `C:\work\boatrace\config\exclusions.json`
- excluded_jcd（運用ON）: `03,06,07,08,11,12,13,14,16,18,19,20,21,23,24`（15場）
- 根拠（固定窓 2025-10-08..2025-12-30 / CAP10+EXCL10 v2 what-if）:
  - core3（追加: 19,21,24） ROI=1.640620
  - core5（追加: 19,21,24,13,16） ROI=1.693739 ※採用
- 本採用後の再現: `run_candidate_cap10_excl10.ps1` → ROI=1.693739（key_overlap_rate=1.0000）

### 追加検証（ローリング窓 / 2026-01-06 実施）
- payouts_fixed: `C:\work\boatrace\runs\payouts_all_2025-10-02_2025-12-30_MERGED_keynorm.csv`
- 窓別ROI（core3=Core5から{13,16}を外した比較対象 / core5=現行運用）:
  - W1_30d（2025-10-08..2025-11-06）: core3=2.11044 / core5=2.11044（同等）
  - W2_30d（2025-11-07..2025-12-06）: core3=1.31322 / core5=1.30454（core3僅差）
  - W12_60d（2025-10-08..2025-12-06）: core3=1.71048 / core5=1.70612（core3僅差）
  - W3_30d（2025-12-01..2025-12-30）: core3=1.21756 / core5=1.35425（core5明確に優位）
- 結論：**直近30d（W3）で core5 が明確に勝つ**ため、運用は core5（現行 `exclusions.json`）を継続採用する。


## 固定窓比較（worldline固定のための手順）【重要】
- 目的：ticketsの期間が伸びても「比較窓」を固定し、世界線ズレ（ROIブレ）を防ぐ。
- 手順（例）：
  1) tickets を窓でフィルタ（例: 2025-10-08..2025-12-30）
  2) その tickets に対して CAP10+EXCL を適用（deterministic v2）
  3) 同一 payouts（同一窓/同一キー）で ROI を計算
- この比較で key_overlap_rate=1.0000 を満たすことを必須とする。

## 必須ドキュメント（bundle同梱必須）
チャット切替時の世界線ズレ・手順迷子を防ぐため、以下は **HANDOVER_BUNDLE に必ず同梱**されること。
欠けている場合は **仕様違反として検出して失敗**させる（mandatory_docs_guard）。

- COMMUNICATION_RULES.md
- USER_TENDENCIES.md
- SPEC_FIXED.md
- IMPORTANT_ELEMENTS.md
- RUNBOOK_PREP.md
- RUNBOOK_PRACTICE.md
- TRACK_EXCLUSIONS.md
- LEDGER.md
- ERROR_COOKBOOK_BOATRACE_CAP10.md
- B_ONLY_RULE.md

## P0近接ミス（near-miss）改善：Rule24（外枠ケア・3連複1本差し替え）
- 目的：3着に5/6が来る「近接ミス」を拾う（**買い目の総点数は増やさず**、3連複の1本を差し替えるだけ）
- トリガー（非オラクル／公式featuresのみ）：
  - lane5 または lane6 が **展示タイム順位<=3 かつ ST順位<=4**
  - 対象レースの 3連複（active=1）のうち **cand1側の1本だけ** を「axis1-axis2-outer(5/6)」に差し替え
- 2025-10-08〜2025-12-30（active 5653R）での検証結果：
  - 適用率：26.9%（1522R）
  - ROI：1.076 → **1.097**
  - 収支差：+409,900円（投資額同一）
- 実装方針：**検証ネタ（トグル可能）として追加**し、運用へ混ぜる場合は「ケア枠」と明記（デフォルトOFFのままでもOK）。

## 検証ネタ（デフォルトOFF）: Rule24 / HIT_LOSS配分（CAP10/core5想定）

- Rule24（外枠ケア）:
  - 5/6号艇が `disp_rank<=3 & st_rank<=4` を満たし、かつ axis/cands と被らない場合、
    3Fの `axis1=axis2=cand1` を `axis1=axis2=outer(5or6)` にswapする（総投資・点数維持）。
  - CAP10_LOCK(2025-10-08〜12-30)ではROIはほぼニュートラル（微減）、命中率は微増。

- HIT_LOSS配分（P0候補）:
  - Aのみ、`axis1_st_rank>=3 or axis2_st_rank>=3` のとき 3T/3Fを 80/20→60/40へ寄せる（総投資維持）。
  - CAP10_LOCKでROI +0.012（概算）と改善が見えたため、次は丸め込み実装のP0として扱う。

（詳細は SPEC_FIXED.md の「追加メモ」参照）


## 重要要素（追加）: ベースライン関連スクリプト／バッチの変更ガード
- 実践フロー・30d/90d検証のベースラインに関わるスクリプト／バッチは、**合意後にのみ** 新規作成・更新する。
- チャット内での再計算や原因切り分けで当該スクリプト／バッチが必要な場合、**効率/精度が大幅に上がると判断できる場合に限り**、アップロードを提案する。

## 重要要素（追加）: 90D検証のCANON化がCフェーズへ与える副作用（注意事項）

### 結論（先に）
- 90D検証としての「CANON化（正本化）＋旧版退避」は正しい。
- ただし **Cフェーズ側に “固定名ファイル直下参照” の依存が残っている場合、CANON化が副作用でCを壊し得る**。
- よって当面の方針は「Cが参照する固定名は残す」こと（中身はCANONへ委譲する）。

### 何が起きるか（副作用）
- 90Dでファイル名変更・退避・配置替えをすると、C側のワンボタン/ラッパーが
  - 固定名（例：特定の runs 直下ファイル名）
  - 固定パス（特定ディレクトリ直下）
  に依存している場合、Cの入口が壊れる（“ファイルが無い” 事故に見える）。

### 再発防止（未実装の方針：どちらかで吸収）
- 方針A（推奨・影響小）：**固定名は残す**。固定名ファイルは “薄いラッパー” とし、内部でCANONを参照して処理する。
  - 例：run_onebutton_* は固定名の入口を維持し、中で `CANON_INDEX` など “最新参照” に委譲する。
- 方針B（影響大）：Cフェーズ自体を参照型へ改修し、固定名依存を排除する（CANON_INDEX参照など）。

### 運用ルール（重要）
- 90D側でCANON化・退避を実施した場合、**「C側の固定名依存があるか」を必ず注意事項として引継ぎに書く**。
- 現時点では「大改修はしない」。副作用は注意事項として固定し、将来のP0/P1タスクで吸収する。

