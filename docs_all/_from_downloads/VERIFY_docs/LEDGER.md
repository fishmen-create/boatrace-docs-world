# 台帳（対応予定タスク / 有効打 / 保留）
- [P0] 実行ファイルへ「HIT_LOSS配分（Aのみ・ST>=3・60/40）」を組み込み（cap10+core5のtickets生成に反映）
## 原則
- 台帳はチャットを跨いで必ず引継ぎに含める（全文貼付は不要、必要なら要点のみ）
- 追加したら「目的・期待効果・トリガー・必要入力・評価指標」を最低限書く

## TODO

- [TODO / 次チャット] `cap10_select_conf_top10_v3.py` の `columns overlap but no suffix specified: ['date','jcd','race_no']` を根治
  - 原因：pandas merge/join でキー列が重複（suffix未指定）
  - 対策：join前に右側の `date/jcd/race_no` を drop する or suffix 付与
  - ERROR_COOKBOOK に「この表現のまま」追記して再発時に迷子にならないようにする
（優先順）
- [P0] 安全設計付きワンボタン化
  - 目的：payout二重起動防止 / b_only分岐 / 正本入力優先 / 期間寄せ / dedup+preflight+backtestまで一括
  - 成果物：改修版bat（run_onebutton_safe.bat等）、ロック機構、dry-runチェック
  - リスク：二重起動、期間ズレ、入力正本の取り違え
- [P2] payout収集の時間短縮（差分DLでも数時間かかる問題の改善）
  - 目的：payout更新（例: 5日分）が 2〜3時間以上かかるのを短縮し、運用のボトルネックを減らす
  - 案（候補）：
    - 取得の並列化（レース/日単位でワーカー化）＋リトライ/レート制御
    - キャッシュ粒度を日単位にして「未取得日だけ」を高速にスキップ可能に
    - 取得対象の分割（場/日）と resume を前提に、停止→再開を堅牢化
  - 完了条件：5日分の更新が“現状より大幅に短い”時間で安定完走（ログと実測で確認）

- [P2] バックテスト時の RuntimeWarning（Mean of empty slice）の是正
  - 症状：numpy の RuntimeWarning が大量発生しログが汚れる（例: Mean of empty slice）
  - 方針：warning抑制ではなく、空配列が出る原因をガードして “計算が意味を持つ” 形に修正
  - 案（候補）：
    - nanmean 等の前に len==0 をチェックして NaN/0 など仕様通りに返す
    - prune / フィルタ後に空集合になるパスを preflight で検知して早期continue
    - どうしても不可避な場合のみ、対象warningを局所的にfilter（影響範囲を限定）
  - 完了条件：通常運用の backtest 実行で当該 warning が出ない（または意図した最小件数のみ）

## 検証ネタレジストリ（デフォルトOFF / what-ifのみ）
- 原則：**1レースで方針を変えない**。気づきは「検証ネタ」として **即登録（状態=OFF）**し、実運用には反映しない
- 類似ネタは **同一IDに集約してカウント（複数日合算）**し、検証の優先度に反映する
- 優先度（目安）：
  - P1：count>=3（複数日合算）…検証優先
  - P2：count==2
  - P3：count==1（観測継続）
- 採用ゲート：what-ifバックテストで **30日ROI＋件数（例:20R以上）** を満たしたものだけ ON（恒久反映）



### ID: HYP_ALLOC_3F3T_RATIO_SA_COMBINED
- 状態: OFF（保留：BLで悪化 / BTで改善と世界線で符号が割れるため、恒久反映しない）
- 優先度: P2（count=1）
- タグ: allocation, 3F, 3T, sa_combined, whatif
- 仮説: S/Aを合算しても、3連単(3T)と3連複(3F)の投資比率を調整すればROIが改善する可能性（総投資は各レース固定）
- 介入（what-if定義）: 1レースあたり総投資は固定のまま、3F/3Tの比率だけを差し替え（連続配分=理論値。丸め込みは別検証）
- トリガー: なし（全S/A対象）
- 必要入力: tickets_long（bet_yen / bet_type / hit判定）＋ payouts（払戻）
- 検証: BL/BTで同期間・同payoutsで比率をスイープしてROI差分を見る（世界線で符号が割れないか確認）
- 評価指標: ROI差分、profit差分、件数（最低20R以上／推奨は30日窓）
- 観測: count=1 / last_seen=2026-01-14

**検証結果（90D / 2025-10-02..2026-01-10 / S+A合算）**
- BT（CAP10+EXCL）
  - baseline ROI=0.718446（inv=10,040,000 / ret=7,213,200）
  - 3F/3T=40/60 ROI=0.720010（ΔROI=+0.001564）
  - 3F/3T=50/50 ROI=0.720792（ΔROI=+0.002346）
  - 3F/3T=60/40 ROI=0.721574（ΔROI=+0.003127）
- BL（analysis）
  - baseline ROI=0.624403（inv=92,460,000 / ret=57,732,300）
  - 3F/3T=40/60 ROI=0.618231（ΔROI=-0.006172）
  - 3F/3T=50/50 ROI=0.615144（ΔROI=-0.009259）
  - 3F/3T=60/40 ROI=0.612058（ΔROI=-0.012345）

**結論（台帳記録）**
- 判定: HOLD（保留）
- 理由: BTでは改善するが、BLで一貫して悪化。世界線で符号が割れるため恒久反映しない。





### ID: HYP_A_PRUNE_MIYAJIMA_WAVE23_OR_R58
- 状態: ON（暫定：宮島のみ。A-として見送り。※Sは常に採用）
- 優先度: P2（count=0）
- タグ: miyajima, wave_cm_2to3, race_no_5to8, A_minus_prune
- 仮説: 宮島など一部場で「波高2〜3cm」または「5〜8R」を A- として見送ると、AのROIが改善する可能性
- トリガー: (wave_cm in {2,3}) OR (race_no in {5,6,7,8})  ※適用場はconfigで限定
- 必要入力: 波高（直前）、レース番号
- 検証: A_pruneをON/OFFしたwhat-if比較（場別/期間別）
- 評価指標: AのみROI、全体ROI、件数（30日>=20R目安）
- 観測: count=0 / last_seen=-
- 検証結果（replay what-if / 2025-12-03..2025-12-30 / payout covered=2832R）:
  - BASE: invest=28,320,000 / return=20,600,200 / ROI=0.727408 / profit=-7,719,800
  - HYP : invest=27,420,000 / return=20,254,000 / ROI=0.738655 / profit=-7,166,000
  - ΔROI=+0.011247 / Δprofit=+553,800（※investが減るためprofit差で評価）
  - 影響範囲: affected=114R（宮島×Aのみ、wave{2,3}またはR5-8）

### ID: HYP_OUTER_CARE_TRIGGER
- 状態: OFF（保留：現行の差し替え方式では効果が小さくブレやすい。デフォルトOFF継続）
- 優先度: P3（count=0）
- タグ: outer_lane, tenji_rank_top2, st_rank_top2, shallow_in
- 背景: コース優先＋ST/展示ペナルティ弱めを一般化するとROI悪化の傾向があったため恒久実装はしない（ただし例外的に有用な可能性）
- 仮説: 外枠が「展示上位＋ST上位」で、かつ進入が深くない場合に限り、3着ケアとして薄く拾うと取り逃しが減る
- トリガー（例）: lane in {5,6} AND tenji_rank<=2 AND st_rank<=2 AND (進入が深くない)
- 必要入力: 展示タイム/展示ST、進入、風/波
- 検証: トリガー該当レースのみで what-if のROI差分（全場/場別）
- 評価指標: ROI差分、件数（該当20R未満は保留）
- 観測: count=0 / last_seen=-
- 検証結果（replay what-if / 2025-12-03..2025-12-30 / payout covered=2832R）:
  - トリガー該当（covered）=516R / 実際に買い目変更=153R（多くはaxis一致/既に3Fに含むため）
  - BASE: invest=28,320,000 / return=20,600,200 / ROI=0.727408 / profit=-7,719,800
  - HYP : invest=28,320,000 / return=20,658,000 / ROI=0.729449 / profit=-7,662,000
  - ΔROI=+0.002041 / Δprofit=+57,800（invest不変）
  - 注意: 3Fの1点を差し替える方式のため「当たりを拾う」反面「元の当たりを落とす」も発生（gain 11R / loss 21R）

### ID: HYP_TENJI_FAST_PROMOTE
- 状態: ON（暫定：安全枠3連複で trigger艇を必ず含める。※予算据え置きで差し替え）
- 優先度: P1（count=20）
- タグ: tenji_time_rank1, st_rank_top3, safety_include
- 仮説: 「展示タイム1位 かつ ST上位」の艇は、ケア枠ではなく **安全枠（3連複）には必ず含める** と取り逃しが減る
- トリガー: tenji_time_rank==1 AND st_rank<=3
- 必要入力: 展示タイム/展示ST（直前）、進入変更（任意）
- 検証: 30日/90日 what-ifで safety_include をONにした場合のROI差分
- 評価指標: 全体ROI、S/A別ROI、件数（30日>=20R、90日>=60R）
- 観測: count=20 / last_seen=2026-01-05
  - live: 平和島2R（2026-01-05, 結果: 1=3=5）/ 多摩川5R（2026-01-05, 結果: 1=2=4）
  - replay: 2025-12-03 {住之江1R/5R/7R, 大村5R, 宮島7R/11R}（trigger艇が3着内だが候補セット外）
  - replay: 2025-12-08 miss=12件（HYP_TENJI_FAST_PROMOTE_miss12.csv）

**直近の検証（payouts未使用 / 結果=finishから的中判定のみ）**
- 対象期間: 2025-12-03〜2025-12-30（S/A候補 4,226R）
- 介入内容: trigger艇（展示1位＆ST上位3）が候補セット(axis1/axis2/cands)に無い場合、**安全枠(3連複)の2本目**をその艇に差し替え（予算据え置き）
- 変化:
  - Hit(any): 1,144/4,226 (27.07%) → 1,198/4,226 (28.35%) **+54R (+1.28pt)**
  - 内訳: gain 88R / loss 34R（net +54R）
- 次アクション: payoutsが揃い次第、同じ介入で **ROI差分** を算出して採否判断（30日>=20R / 90日>=60R）

## DONE（完了ログ）
- （ここに完了したタスクを移動）
---

## 2026-01-05 検証結果（payouts反映 / ROIで本判定）

### HYP_TENJI_FAST_PROMOTE（P1 / count=8）
- 内容：展示最速（display 1位）かつ ST上位（<=3位）の艇が、候補セット（axis1/axis2/cands）に入っていない場合、**安全枠(3連複)に含める**（3連単は触らない）
- 検証期間：2025-12-03..2025-12-30（BT_PSEUDO_20251203_1230 の S/A 4,226R）
- payoutファイル：payouts_all_2025-12-03_2026-01-01.csv
- payoutカバレッジ：S/A内 2,832/4,226 = 67.0%（未取得分あり）

**結果（payoutカバレッジ内で評価）**
- Baseline ROI: 0.72741  →  New ROI: 0.73814  （ΔROI = +0.01073）
- Invest: 28,320,000 / Return: 20,600,200 → 20,904,200（ΔReturn +304,000）
- 介入発生：415R（needs_add=True かつ payoutあり）で **ROI 0.557 → 0.630（Δ +0.073）** に改善

**暫定判断**
- 「当たりを増やす」だけでなくROIも改善傾向。ただしpayout欠落が33%あるため、**payout取得が揃った状態で再実行して確定**が望ましい。
- 運用反映は現時点では **検証ネタ（デフォルトOFF）を維持**。次に full payouts で再検証→採用判定。

（出力）
- hyp_roi_summary_HYP_TENJI_FAST_PROMOTE_20251203_1230.txt
- hyp_roi_compare_HYP_TENJI_FAST_PROMOTE_20251203_1230.csv

## 派生検証ネタ（TENJI派生）
目的：HYP_TENJI_FAST_PROMOTE（暫定ON）の“次の一段”として、適用範囲を絞ってもROIを維持/改善できるか、または外枠は別設計（追加ケア）に分けた方が良いかを検証する。いずれも **デフォルトOFF（what-if専用）**。

根拠（covered=2832R / 2025-12-03..12-30）：
- 現行（全modified適用）：ROI 0.738143（ΔROI +0.010734 / Δ回収 +304,000円, apply_modified=415）
- Aのみ：ROI 0.736727（ΔROI +0.009319 / apply_modified=359）
- 内(1-3)のみ：ROI 0.734629（ΔROI +0.007221 / apply_modified=231）
- 外(5-6)のみ：ROI 0.731275（ΔROI +0.003867 / apply_modified=110）

### 派生ネタ一覧（OFF）
- [P2][OFF] DER_TENJI_A_ONLY  
  - 内容：TENJI補正は **Aランクのみ**に限定（Sは現行のまま/または補正しない what-if）
  - 期待：適用範囲を減らしてもROI改善を保てるなら、ブレ耐性と運用の単純化に寄与
  - 追加検証：60d/90dで再現、S側の悪化がないか
- [P2][OFF] DER_TENJI_INNER_ONLY  
  - 内容：TENJI補正は trigger_lane ∈ {1,2,3} のときだけ適用（内寄り限定）
  - 期待：外枠の取り逃し/相殺を抑えて“効く領域だけ”残す
- [P3][OFF] DER_TENJI_OUTER_AS_ADDITIVE_CARE  
  - 内容：trigger_lane ∈ {5,6} のときは「差し替え」ではなく **ケア枠として少額追加**（安全枠を潰さない）
  - 期待：外枠は差し替えでlossが出やすいため、追加方式に分離して改善できる可能性
  - 注意：点数/予算が増えるので、cap・点数制約とセットでwhat-ifする

出力（このチャットで生成）：
- tenji_derived_variant_eval_20251203_1230.csv
- tenji_derived_segments_lane_tier_20251203_1230.csv
- tenji_derived_top_tracks_20251203_1230.csv
- tenji_derived_top_days_20251203_1230.csv

## P1: 除外場の設定ファイル化（引継ぎ必須）
- 目的：除外場（exclude_jcd）が検証/運用結果に直結するため、チャット切替で漏れないよう正本化する
- 正本：docs/TRACK_EXCLUSIONS.md（説明）＋ config/exclusions.json（機械可読）
- 実装：backtest/予想の実行時に --exclude-jcd を必ず渡し、サマリ/レポートに exclude_jcd を明記（空でも none）
- ステータス：未完（除外リストの確定が必要）
- 追加：generate_handover.ps1 の対象ファイルに TRACK_EXCLUSIONS.md を含める

## P1: 重要要素（未採用でも引継ぎ必須）の正本化・自動吸い上げ
- 目的：チャット切替で「未採用だが重要」要素（除外場/CAP/期間ズレ/欠損/二重起動防止など）が漏れるのを仕組みで防ぐ
- 正本：docs/IMPORTANT_ELEMENTS.md（定義・必須ファイル一覧）
- 対応：
  - generate_handover.ps1 の対象ファイルに IMPORTANT_ELEMENTS.md / TRACK_EXCLUSIONS.md を追加
  - HANDOVER 出力に「重要要素の条件（exclude_jcd, cap, date range）」を必ず明記（空でもnone）
- ステータス：進行中（重要要素の網羅とスクリプト反映が未完）


---

## [PENDING] 自動ガード：期間カバレッジチェック（payouts × features）

- 追加日: 2026-01-05
- 背景: payouts の中身（date範囲）が features の検証期間を含んでいないケースがあり、key overlap=0 / Return=0 の“事故”が発生し得る（ファイル名が紛らわしい/取得途中/マージ違いなど）。
- 目的: 人手のmin/max確認に依存せず、**backtest開始時に自動で弾く**（fail-fast）ことで再発を仕組みで潰す。

### 実装案（最小）
1) backtest 起動時に features_csv と payouts_csv を読み込み、
   - features: min(date), max(date)
   - payouts : min(date), max(date)
2) `payouts.min_date > features.min_date` または `payouts.max_date < features.max_date` の場合は **即エラー終了**
   - エラー文に「不足している期間」「正しいpayouts候補の探し方（min/max確認）」を表示

### 追加案（任意）
- (date, track_norm, race_no) の key overlap が一定未満（例: <70%）なら Warning を出す（実行は継続）

### 評価/完了条件
- 意図的に“期間不足payouts”を渡すと、backtestが開始前に停止し、原因が分かるメッセージが出る
- 正常なpayoutsでは従来と同じ結果が出る（挙動非変更）

### 優先度
- 低〜中（運用ルール＆docsで再発防止は済。仕組み化でさらに固める）

- [P1][高] **Rule24(Aのみ) × HIT_LOSS配分(60/40)((軸1|軸2)ST>=3) の実行ファイル反映（保留中）**
  - 状態：ドキュメント反映済み／実装は保留（要望により）
  - 目的：AのHIT_LOSS抑制＋ROI改善（P0母集団ではCOMBINEDで悪化なし）
  - 実装イメージ：
    - Rule24：Aのみ、外枠(5/6)が disp_rank<=3 & st_rank<=4 のとき 3Fを1点差し替え
    - HIT_LOSS配分：Aのみ、(axis1|axis2)_st_rank>=3 のとき 3T:3F 投資比率を 60:40 へ寄せ（合計投資は固定）
  - 次の判断材料：**core5除外＋CAP10** の tickets_long で同様のwhat-ifを再計測して、採用可否を確定

## 2026-01-08 実施メモ：CAP10_LOCKで Rule24 / HIT_LOSS を評価（完了）

- 入力：
  - tickets_long: CAP10_LOCK_20260107_025047_tickets_long.csv（2025-10-08〜2025-12-30）
  - payouts: payouts_all_2025-10-02_2026-01-05_MERGED_keynorm.csv
  - features: official_features_all_2025-10-08_2026-01-05_dedup.csv
- 結果（概算）：
  - BASE ROI 1.4080
  - Rule24 only ROI 1.4053（ほぼニュートラル）
  - HIT_LOSS only（A & (axis1|axis2) ST>=3, 3T:60%）ROI 1.4201（+0.0121）
  - Rule24 + HIT_LOSS ROI 1.4158（+0.0078）

### 次の優先タスク（高）
- [ ] HIT_LOSS配分を「丸め（100円単位）込み」で実装（トグル化、diagnostic出力（60/40））
- [ ] Rule24はトグルのまま（採用可否は“効果が小さい”前提で運用判断）

- 2026-01-08: HIT_LOSS配分（Aのみ・STランク条件・60/40）を実践採用方針で反映。
  - 実行ファイル反映パッチは v3 を正（v2 は WorkDir/RunDir 解決が壊れて `races csv not found under C` が出ることがある）。

