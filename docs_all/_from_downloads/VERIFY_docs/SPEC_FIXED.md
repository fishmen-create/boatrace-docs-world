# SPEC_FIXED（固定仕様・運用ルール）正本
最終更新: 2026-01-08

## 0.5 参照インデックス
- 文書全体の索引: `DOC_INDEX.md`
- C（Check準備）の実行虎の巻: `C_CHECK_TIGERBOOK.md`


## 0. 目的
- 目的：全場横断での長期ROI最大化
- 思想：S/Aの「信用性（precision）」を落とさず、取れると判断したレースだけ実践（見送り=abstain OK）
- 制約：1日5〜15R程度（実践運用の上限）

## 1. 入力（固定）
- K（all_k_results*.csv）/ fan / boatrace公式features（official_features_all_*.csv）
- payout（payouts_all_*_MERGED_keynorm.csv）

## 2. 前処理（固定）
- 公式featuresは必ず dedup：
  - key = (date, track_norm, race_no, lane, regno)
- jcd欠損時は jyo → jcd 補完（既存ルールに従う）
- track_norm / machine_key 等の正規化は既存ルールに従う

## 3. スコアリング → ランク（v1.2固定）
- conf閾値：
  - S: conf >= 0.87
  - A: 0.60 <= conf < 0.87
  - 見送り: conf < 0.60
- 1号艇軸縛り禁止（2軸/非1軸でも採用可）
- axis1/axis2：
  - 軸スコア上位2艇（拮抗時は順序入替も買う）

## 4. 対象場（core5除外・固定）
- 運用対象（keep）: jcd = [1, 2, 4, 5, 10]
- 上記以外は除外
- 置き場所：docs/TRACK_EXCLUSIONS.md（ON/OFFが正本）

## 5. CAP（固定）
- 出力するのは CAP10 のみ（CAP15は不要）
- CAP10の選定順序は LOCK を採用
  - 詳細：docs/CAP10_SELECTION_ORDER_LOCK.md

## 6. 投資・買い目（固定）
- 1Rあたり投資額：
  - S: 10,000円
  - A: 5,000円
- 二層（固定）：
  - メイン枠：3連単（3T）
  - 安全枠：3連複（3F）

### 6-1. デフォルト配分（現行）
- S/Aともに、原則 3T:80% / 3F:20% を基準（総額は維持）
  - ※将来この基準を変更する場合、本ルール（6-2）も合わせて更新する

### 6-2. 【採用】HIT_LOSS配分（Aのみ・ST条件・60/40）
- 状態：運用採用（自動反映は「あとでやること」に積む／手動でも運用可）
- 対象：Aランクのみ
- 条件：axis1_st_rank >= 3  **または**  axis2_st_rank >= 3
- 配分：
  - 3T:60% / 3F:40%
- 係数（実装目安）：
  - 3T bet_yen × 0.75
  - 3F bet_yen × 2.00
  - （Aの総額5,000円は維持）

### 6-3. Rule24（外枠ケア）
- 状態：検証ネタ（デフォルトOFF）
- 参考：検証メモは docs/IMPORTANT_ELEMENTS.md / docs/LEDGER.md（csvはruns配下）

## 7. 出力（固定）
- races（CAP10）：*CAP10*_races*.csv
- tickets_long：*CAP10*_tickets_long*.csv
- diagnostic（任意）：差分/near-miss/what-if評価