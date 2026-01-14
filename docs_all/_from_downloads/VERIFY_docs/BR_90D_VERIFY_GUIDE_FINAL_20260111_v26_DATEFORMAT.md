# BR_90D_VERIFY_GUIDE_FINAL v25（2026-01-12）
**目的：初見（90D検証が初めて／新規チャットで前提ゼロ）でも、この1本だけで迷わず90D検証を完走する。**

---

## 0. まず最初に読む（Quick Start：最短で完走する）
### 0-1. この仕様書だけでやる（RUNBOOK_PREPは加速装置）
- 本書は **「判断基準＋実行手順＋復旧手順」** を内包する。
- RUNBOOK_PREP は「コピペ効率」を上げる補助（無くても完走できるのが正）。

### 0-2. 今回の90Dで“やること／やらないこと”
**やること（この90Dで確かめる）**
- **世界線一致**：baseline と candidate が *同じ inputs/期間/前処理/設定* で回っているか
- **最低限の期待値**：全体ROIが最低限プラス（ROI≥1.00）か（※採用判断は別途）
- **偏り検査（Robustness）**：勝ちが「特定期間／特定場／特定conf帯」への過度依存でないか
- **baseline vs candidate 比較**：candidate が baseline を上回る兆しがあるか（ROI/件数/偏り）

**やらないこと（誤解防止）**
- 90Dは「未来のROIを証明」しない。**壊れた世界線を早期に除外し、比較可能にする検査**。

### 0-3. 合格基準（旧版の要点を“先に”置く）
**B. Profitability（最低限の期待値）**
- 全体 ROI ≥ 1.00
- n_bet（投票件数）≥ 1,000（母数が少ない勝ちは採用しない）

**C. Robustness（偏り検査：長期ROI最大に一番効く）**
- **固定窓（30D×3：W1/W2/W3）**：3窓のうち **2窓以上が ROI ≥ 1.00**  
  - 1窓だけ大崩れ（目安：ROI < 0.90）は「黄（要調査）」
- **場別（n_bet ≥ 50 の場）**：ROI < 0.85 が複数ある場合は「黄（要調査）」  
  - ROI < 1.00 の場が出るのは短期では許容（ただし偏りが強い場合は要調査）
- **conf帯（confbins）**：勝ちが単一帯に過度依存している場合は「黄（要調査）」

---

## 1. 用語と正本（ここを揃えると迷子にならない）
### 1-0. C型（運用再現）／再計算型（分析用）の役割分離【重要・確定】

本90D検証では、**C型（運用再現）** と **再計算型（分析用）** を明確に分離して扱う。  
この分離が曖昧になると、件数減少やROI低下を「不具合」と誤認しやすいため、以下を**固定ルール**とする。

#### C型（運用再現 / Cフェーズ正本）
- 目的：その日の**実運用の意思決定**を忠実に再現する
- 処理順：
  1) official_features × fan × policy で **conf算出**
  2) **S/A判定**（S: conf≥0.87 / A: 0.60–0.86）
  3) **場除外（運用都合）**
  4) **CAP10（最大10R・最低保証なし）**
  5) 投票内容（tickets_long）を確定
- 補足：S/A はどちらも「運用上の判断対象」。CAP10・場除外は**運用制約**としてC型にのみ適用する

#### 再計算型（分析用 / 90D検証）
- 目的：モデル構造の**性能評価（ROI・安定性）**
- 処理順：
  1) 90D分の official_features × fan × policy で **confを再計算**
  2) **conf≥0.87 を S相当として抽出**（※S/Aラベルは作らない）
  3) 期間集計（件数・ROI 等）
- 補足：
  - **CAP10は適用しない**
  - **場除外は原則適用しない**（分析目的で使う場合は別軸として明示）

#### 確定ルール（要約）
```text
再計算型（分析用）：
  ・conf≥0.87 の集合で性能評価
  ・CAP10 ❌
  ・場除外 ❌（※別軸なら可）

C型（運用再現）：
  ・S/A判定あり
  ・場除外 ⭕
  ・CAP10 ⭕
```

> 注意：再計算型に CAP10 や 場除外 を直接適用すると、  
> 「性能が悪い」のか「制約で削られた」のかが判別不能になるため、原則禁止とする。

### 1-1. 世界線（90D検証の“世界線”）
この節で言う「世界線」は、**「今回の90D検証（v1.2 backtest）の世界線」**を指す。  
具体的には **inputs（features/payouts）・date-from/to・前処理（dedup/keynorm）・設定（policy/exclusions/a_prune 等）**の組。

### 1-2. T_end / T_start（期間の正の決め方）
- **T_end = all_k_results.csv の max(date)**（Kが存在する最終日）
- **T_start = T_end - 89日**（90D＝90日分）

> **実行日 又は 実行日前日 が取得元に存在しない場合、取れないのは自然（結果が掲載されていない可能性あり）**  
> → その場合でも **T_end は「Kのmax(date)」に合わせる**（無理に実行日を入れない）

### 1-3. 正本（Inputsの正）
- **all_k_results.csv**：期間決定の正本（これがズレると全部ズレる）
- **payouts_all_*.csv**：結果（払戻）の正本（期間は必ずT_start..T_endに一致）
- **official_features_all_*.csv**：特徴量の正本（期間は必ずT_start..T_endに一致、dedup必須）

---

## 2. 90D検証の入力・出力（一覧で把握）
### 2-1. INPUT一覧（欠損時の復旧もここに書く）
| 種別 | ファイル | 役割 | 欠損時の復旧（どれを実行？） |
|---|---|---|---|
| K集約 | all_k_results.csv | 期間決定の正本 | **merge_k_results.py** で再生成（3章） |
| 払戻 | payouts_all_{T_start}_{T_end}.csv | 結果（払戻） | **collect_boatrace_payouts.py** で再取得（4章） |
| 公式特徴 | official_features_all_{T_start}_{T_end}.csv | 展示/ST等 | 公式features収集スクリプトで再取得（5章） |
| baseline | baseline_* / tickets_long.csv | 比較基準 | Cフェーズ再生成 |
| candidate | candidate_* / tickets_long.csv | 評価対象 | Cフェーズ再生成 |

### 2-2. OUTPUT一覧（中間含む）
- `runs\DATA_90D_{T_start}_{T_end}\`
  - `payouts_all_*.csv`（中間成果物：結果データ）
  - `payouts_runlog_*.txt`（進捗・失敗切り分けのため必須）
  - `official_features_all_*.csv`
  - `*_tickets_long.csv`（baseline/candidate）
  - `report.csv` / `summary_*.csv`

---

## 3. Step0〜StepN（一本道フロー：ここだけ順に叩けば完走）

> ここでは「各Stepの **使用スクリプト**／**成功条件**／**失敗時の戻り先**」を明示する。

### Step0. 作業場所と前提
- 作業ディレクトリ：`C:\work\boatrace`
- 仕様：v1.2（S/A閾値・dedup規約など）
- 90Dは「世界線一致」が最優先

**成功条件**：`C:\work\boatrace` で作業できる  
**失敗時**：ディレクトリを確認（PowerShellのカレント）

---

### Step1. K（all_k_results.csv）を正本として確定する
**使用スクリプト**
- （必要なら）`download_mbrace_k.py`
- `merge_k_results.py`

**やること**
1) KTXTの格納場所を確認（例：`C:\work\boatrace\mbrace_k_results`）
2) `merge_k_results.py` で `all_k_results.csv` を再生成
3) `max(date)` を取り **T_end を確定**する

**成功条件**
- `all_k_results.csv` の `max(date)=T_end` が取得できる

**失敗時（典型）**
- `merged files : 0` → **INPUT_DIRが違う**（KTXTが無い）
  - 戻り先：Step1（INPUT_DIR再確認）
- `max(date)` が空 → `all_k_results.csv` が壊れている／列名違い
  - 戻り先：Step1（再生成）

---

### Step2. 90D期間を確定する（T_start..T_end）
**使用スクリプト**
- なし（計算・設定のみ）

**やること**
- `T_start = T_end - 89日` を確定し、以後すべての取得・検証をこの範囲に固定

**成功条件**
- date-from/to を迷わず埋められる（T_start, T_endが確定）

**【重要】date-from / date-to の書式は `YYYY-MM-DD`（ハイフンあり）で統一する。`YYYYMMDD` を渡すと、日付パースの不一致によりデータが0件になる等の“サイレント縮退”が起こり得る。**

**失敗時**
- date-to を「実行日」にしてしまう → Kが無ければズレる
  - 戻り先：Step1（T_endをKで再確認）

---

### Step3. payouts取得の“疎通”を先にやる（短期チャンク）
**使用スクリプト**
- `collect_boatrace_payouts.py`（90Dで使う版は白名单参照）

**重要（時間）**
- **payouts取得は1日分あたり約1時間**かかることがある  
- 90Dは数十時間になり得るため、**短期チャンクで疎通→本番**が基本

**成功条件**
- 短期チャンクで `rows>0` が返る（開催がある範囲）
- runlog が出る

**失敗時（典型）**
- `rows=0`：
  - その期間に開催が無い可能性（正常）／取得失敗の可能性（異常）
  - 判定は 6章（rows=0切り分け）へ
- 1KB程度のCSVしか出ない：
  - 異常（取得失敗の可能性が高い）→ 6章へ

---

### Step4. payouts 90D本番取得（長時間）
**使用スクリプト**
- `collect_boatrace_payouts.py`

**やること**
- `[T_start, T_end]` で本番取得
- runlogで進捗確認（途中で止まったように見えるのは通常あり）

**成功条件**
- `payouts_all_{T_start}_{T_end}.csv` が生成され、サイズが極端に小さくない
- runlogに進捗が継続して記録される

**失敗時**
- 6章の「止まった／進まない」切り分けへ

---

### Step5. official_features を取得する（期間一致＋dedup）
**使用スクリプト**
- `collect_boatrace_official_features_*`（環境の正を使用）

**必須ルール**
- 期間は必ず `[T_start, T_end]`
- `official_features_all_*` は (date, track_norm, race_no, lane, regno) で **dedup**

**成功条件**
- 指定期間の features が揃い、dedupルールが満たされる

**失敗時**
- 期間ズレ → Step2へ戻る（期間固定が先）
- dedup未実施 → dedup手順を適用

---

### Step6. baseline / candidate で90D backtestを回し、P0チェックで世界線一致を確認
**使用スクリプト**
- 90D backtest 実行スクリプト（運用の正を使用）
- compare / P0チェック（run_true90_compare.ps1 等、運用の正を使用）

**成功条件**
- P0チェック PASS（ex_rows=0, ex_active_rows=0, ex_bet_sum=0 など）
- baseline/candidate が同一inputs・同一期間で比較できる

**失敗時**
- inputs/期間ズレ → Step1-5を疑う（特にT_end）
- exclusionsズレ → configの正本確認（候補/基準の差分を明示）

---

## 4. 90Dで使うスクリプト（白名单：誤爆防止）
※環境に複数版がある場合でも、**90Dではこれだけを使う**。

| 役割 | スクリプト | 入力 | 出力 |
|---|---|---|---|
| K取得 | download_mbrace_k.py | date-from/to | KTXT |
| K集約 | merge_k_results.py | KTXTディレクトリ | all_k_results.csv |
| 払戻取得 | collect_boatrace_payouts.py | all_k_results.csv + date-from/to | payouts_all_*.csv + runlog |
| features取得 | collect_boatrace_official_features_* | all_k_results.csv + B | official_features_all_*.csv |

---

## 5. 注意点（時間・進捗・再開前提）
- payoutsは長時間：**1日≈1時間**（環境・取得状況で変動）
- 90Dは数十時間：**途中停止／再開前提**で運用する
- 進捗確認は runlog を正にする（コンソール表示だけに依存しない）

---

## 6. トラブル切り分け（今回の詰まりを仕様に昇格）
### 6-1. rows=0 は正常か？異常か？
- 正常の可能性：その期間に開催が無い（特に単日・特定場）
- 異常の可能性：取得失敗（HTML/ブロック/タイムアウト/パース失敗）

**判断の最短ルート**
1) 範囲を「開催がある」日付に寄せて再実行（短期チャンク）
2) runlogに progress が出ているか確認
3) それでも rows=0 が続くなら取得失敗寄り

### 6-2. 1KBファイルが出た
- 原則 **異常**（取得が途中で落ちている可能性が高い）
- runlogを確認し、例外なく切り分けする

### 6-3. 「止まって見える」
- runlogの末尾が更新されていれば **進行中**
- 更新が止まっているならネットワーク／取得元応答／リトライ設計を疑う

---

## Appendix A. 参照（運用ルールの固定仕様 v1.2）
- 予想：K + fan + official_features → S/A
- 1号艇軸縛り禁止（2軸/非1軸OK）
- conf：S>=0.87 / A=0.60–0.87 / 見送り<0.60
- official_features_all_* は (date, track_norm, race_no, lane, regno) でdedup
- D直前：スタート展示Fは切り根拠にしない（ルールAのみ）
