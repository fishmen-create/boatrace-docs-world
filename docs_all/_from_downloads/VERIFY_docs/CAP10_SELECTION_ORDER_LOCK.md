# CAP10 選定順序ロック（検証用）

目的：**検証の再現性を担保**するため、CAP10（=上位Kレース選定）の「選び方（順序）」を明文化し、毎回同一の入力なら同一の出力（selected_races / cap tickets）になる状態を作る。  
※運用ルールとしての確定ではなく **検証時のロック**。

---

## スコープ

- 対象：CAP10（上位K）＋除外場（`config/exclusions.json`）を適用して **cap tickets** を生成する工程
- 前提：入力 tickets は **bet_type / combo / bet_yen_eff** を含む（ROI計算が可能な形式）

---

## 1) 入力（Source of truth）

1. **Tickets 入力**  
   例：`C:\work\boatrace\runs\backtest_alltracks_YYYY-MM-DD_YYYY-MM-DD_*_tickets_long.csv`

2. **除外場（source of truth）**  
   `C:\work\boatrace\config\exclusions.json` の `excluded_jcd`

3. **CAP10 実装**  
   `C:\work\boatrace\make_cap10_excl_tickets_v2.py`（このファイル内容が「仕様」）

---

## 2) CAP10 の選び方（順序）の固定ルール

### 2-1. レース単位にまとめる
- tickets を **(date, jcd_norm(or jcd), race_no)** でレース単位に集約し、投資額（`bet_yen_eff` 合計）を算出する  
  ※3T/3Fなど券種は混在してOK。レース単位の投資合計で cap を判定する。

### 2-2. 除外場を適用
- 集約前/後のどちらでもよいが、最終的に **excluded_jcd のレースは候補から除外**する

### 2-3. 「順位」(rank) の決め方（最重要）
**検証では以下の優先順位でレースをソートして上位Kを取る：**

1) `daily_cap_priority`（存在する場合）：昇順（例：`tier_conf` が最優先）  
2) `daily_cap_rank_y`（存在する場合）：昇順（小さいほど上位）  
3) `tier`（存在する場合）：**S → A → その他** の順  
4) `conf`/`score` 相当（report 由来など：存在する場合）：降順（高いほど上位）  
5) タイブレーク（必ず固定）：`date` → `jcd_norm(or jcd)` → `race_no` 昇順

> 注：`daily_cap_priority` / `daily_cap_rank_y` が tickets 側に既に付与されているなら、**それを最優先で信頼**する（同じ入力なら同じ並びになるため）。  
> report を使って順位を付ける場合も、最終タイブレークは固定する。

### 2-4. 上位Kの選定
- 各日（date）ごとに上位Kレースを選ぶ（例：K=10）
- これを `selected_races_*.csv` として出力し、cap tickets を作る

---

## 3) 検証で必ず残すもの（ロック情報）

- tickets 入力ファイル：パス + SHA256
- exclusions.json：パス + SHA256 + excluded_jcd の中身
- make_cap10_excl_tickets_v2.py：パス + SHA256
- 実行コマンド（--tickets / --out / --selected-out / --k / --exclude-jcd / --report）

---

## 4) 運用への影響（誤解防止）

- これは **「検証でブレない」ための固定**  
- これをそのまま運用へ流用するかは任意（流用すれば“淡々と回す”運用になりやすい）
