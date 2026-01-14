# SPEC_FIXED（固定仕様・運用ルール）正本

> 迷子防止：困ったら `docs/DOC_INDEX.md` → 該当ドキュメントへ。
> C（Check準備）の入口は `docs/C_CHECK_TIGERBOOK.md`。

最終更新: 2026-01-08

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

# 準備パート Runbook（正本）
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

## 追加：source_of_truth（固定化）
- baseline: `C:\work\boatrace\config\baseline.json`
- exclusions（運用ON）: `C:\work\boatrace\config\exclusions.json`
- candidate（CAP10+EXCL deterministic v2）: `C:\work\boatrace\config\candidate_cap10_excl10.json`

# 実践運用フロー（PDCA/CDCA）正本
## 0. ゴール（全工程共通）
- 目的：全場横断での長期ROI最大化
- 制約：1日5〜15R程度（実践運用の上限）
- 思想：説明可能性＞「当てた/外した物語」

## C（Check準備）前日夜〜当日朝：暫定予想
- 入力：K + fan + boatrace公式事前データ（静的）
- 出力：暫定S/A候補、見送り、axis候補、conf

## D（Do）締切15分前：直前再評価
- 入力（ユーザ提供）：展示/ST/波高/欠場/進入変更（＋任意でオッズ歪み）
- AI処理：展示/ST補正、prune判定、最終S/A確定、買い目確定（S厚め）
- 運用採用：HIT_LOSS配分（Aのみ・axis1/axis2のSTランク>=3で 3T:60% / 3F:40%）
- 注意：場別例外（例：A-）は config に従う。全場共通化しない。

## C（Check）結果取得（ユーザ作業）
- payout CSV取得、実投資・実回収の記録（事実確定のみ）

## A（Act）振り返り・改善（AI作業）
- 観点：採用R数、S/A別ROI、conf帯ROI、場別ROI、prune差分
- ルール化：30日ROI＋件数（例:20R以上）で再現したもののみ恒久採用
- 検証ネタはデフォルトOFF（what-ifでのみ扱う）

# コミュニケーション運用ルール（AI↔ユーザ）


## ユーザ負担最小化（必須）
- 依頼は「コピペ1発」または「ファイルアップロード→AI側で処理→DL→上書き」の形を優先する（思考負担を減らす）。
- ローカル実行が必要な場合は必ず **「これはあなたの作業です」** と明記し、具体的な手順（PowerShell/cmdのコマンドまで）を提示する。
- 「ローカルにあるから」で止めず、(A)ローカル実行 と (B)アップロード代替案 の両方を必ず提示し、短期/中期/長期の効率所感も添える。

## 依頼・提案の扱い
- ユーザの依頼/提案は「目的（全場の長期ROI最大化）」「制約（1日5〜15R程度など）」基準で評価する
- 結論は「採用/保留/却下」を明示し、理由を短く添える
- 保留にした有効打は台帳（LEDGER）に記録する（台帳本文表示は重ければ省略可）

## ログ/出力
- 長いログは貼らない（最終数値/ファイルパス/再現コマンド/重要エラー1行）
- コマンド提示はPowerShell/cmdを明示する

## 引継ぎ（HANDOVER）運用：壊れない生成方式（手戻りゼロ優先）

### まず結論（運用ルール）
- **チャット切替の直前は、必ず「1コマンドで HANDOVER.md + zip を生成」してから切り替える。**
- HANDOVER.md は **“docs正本” だけ**をソースにして生成する（ターミナル出力/ログを貼らない）。  
  → これで「ログ混入で壊れる」経路を遮断する。
- 生成後に **lint（汚染チェック）**を必ず通す（usage/Traceback/PS> などの混入を検知したら失敗にする）。

### なぜ壊れたか（混入経路の推定）
- もっとも多いのは **PowerShell/python の標準出力・エラー出力（usage:, Traceback, ParserError など）を、コピペやリダイレクトで HANDOVER.md に混入**させるパターン。
- 次に多いのは **“世界線（baseline/除外/投資列/期間/active条件）” の前提が揃わないまま、別条件の結果を同じ名前で扱ってしまう**パターン。
- さらに、JSON/BOM や 列名差（jcd/track_norm 等）で例外が出たログを貼ると、以後の手順が迷子になりやすい。

### 壊れない生成方式（1コマンド）
1. `generate_handover_bundle.bat` を実行する  
   - HANDOVER.md を生成（docs正本から合成）
   - 混入チェック（lint）
   - zip を runs 配下に出力（新チャットへ持ち込むファイル一式）

> **注意**：チャット内の指示で “複数行コマンド” を貼るより、  
> **bat 1本**に集約して “貼り間違い” を消すのが目的。

### 切替時の必須チェックリスト（コピペ用）
- [ ] `generate_handover_bundle.bat` を実行し、zip の出力パスが表示されている
- [ ] HANDOVER.md の先頭に「今回の世界線（CAP/EXCL/期間/投資列/active条件）」が明記されている
- [ ] ガード（worldline guard）が OK になっている（guardレポートが zip に入っている）
- [ ] 新チャットの最初に、**HANDOVER.md を貼り付ける + zip を添付**した
- [ ] 追加で AI に見せる必要がある大きいCSV（payouts 等）がある場合は「どのファイルをアップロードするか」も HANDOVER に明記した

### 切替提案トリガー（v2：迷子リスク中心）
「体感の重さ」ではなく、迷子リスクで発火する。

【強制発火（1つで切替提案＋HANDOVER_BUNDLE生成）】
- 複数世界線（ROI算出条件/前提）が同時に走り始めた
- ファイル名/パス/列名の揺れでエラーが連続（原因が構造化）
- 「本来の第一手」が見えにくくなった

【切替提案の必須出力（未完でも先に出す／これが揃うまで作業を進めない）】
1) 理由(1–2行：どの迷子リスクが発火したか)
2) 引継ぎコピペ全文
3) 次の最短手順チェックリスト
4) 生成物一覧（ファイル/パス/再現コマンド）

## ルール・方針の記録（忘却防止）
- ユーザ作業は極力「コマンドのコピペ」「指定ファイルのアップロード」など、ユーザの思考負担が少ない“機械的作業”で完結する形で依頼する（手順は具体的・一発で再現可能に）。
- ユーザが「運用ルール」「方針」「制約」「優先順位」を追加・更新した場合、AIは**原則として関連ドキュメント（docs正本）へ記録**する。
- 記録はユーザ作業を極力減らすため、AI側で更新版ファイル/ZIPを生成し、ユーザは**ダウンロード→上書き**で反映できる形を優先する。
- 記録対象の例：payout運用（再利用/差分DL）、worldline guard手順固定、除外場運用、cap運用、切替提案トリガー等。

# ユーザ傾向・特徴（不変の正本）

## 明示的に依頼されたこと（ユーザ要求）

* 依頼/提案は「目的・ゴール基準」で評価（採用/保留/却下を明示）
* 後回しの有効打タスクはメモリではなく台帳（LEDGER）に記録

  * 台帳の全文表示は重くなるなら不要（文章で通知でOK）
  * ただしチャット切替時の引継ぎには台帳を必ず含める

* チャットが重くなる前に、AI側が先回りで切替提案

  * 理由(1-2行)＋引継ぎコピペ全文＋最短手順＋生成物一覧＋省略候補 を必ずセットで出す

* コマンドが必要な手順は必ずコマンド提示（PowerShell/cmdの区別も）
* 長いログは貼らず圧縮（最終数値/ファイルパス/再現コマンド/重要エラー1行）
* 仕様/前提/正本は勝手に変質させない（固定仕様・差分説明）
* “部分差し替え”は原則NG（言語に詳しくないため）。可能なら全文貼り替え手順で提示
* S優先→confはOKだが、Sの下限（最低本数）運用は不要。ランクの信用性は落としたくない
* payout取得など重い処理は先に回しておきたい

## AIが感じた好み・癖（仮説）

* 「次の一手」が明確だと安心：宣言→実行内容→結果の読み方
* 再現できる運用（Runbook/正本/差分）を重視
* 仕様ブレ（どれが正本か不明）を嫌う：spec/runbook/ledger/handoverで統制
* 情報量より要点圧縮が好み：必要十分な結論＋根拠＋次の一手

## 参照優先順位（迷子防止）

1. SPEC\_FIXED.md（固定仕様）
2. RUNBOOK\_\*.md（準備/実践）
3. COMMUNICATION\_RULES.md（会話運用ルール）
4. USER\_TENDENCIES.md（ユーザ傾向・特徴）
5. LEDGER.md（後回しタスク）
6. 実行ログ/一時メモ

## 引継ぎに関する強い嗜好（重要）
- ユーザーは **チャット切替による情報欠落・手戻りを強く嫌う**。
- 切替時は「引継ぎコピペ」だけでなく、**使用している docs正本一式を zip 同梱**すること。
- 迷子防止のため、切替直前に **worldline guard** を通し、HANDOVER に “世界線（前提）” を固定してから次へ進む。

# 台帳（対応予定タスク / 有効打 / 保留）
- [P0] 実行ファイルへ「HIT_LOSS配分（Aのみ・ST>=3・60/40）」を組み込み（cap10+core5のtickets生成に反映）
## 原則
- 台帳はチャットを跨いで必ず引継ぎに含める（全文貼付は不要、必要なら要点のみ）
- 追加したら「目的・期待効果・トリガー・必要入力・評価指標」を最低限書く

## TODO（優先順）
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

# 除外場（Track Exclusions） 正本

## 目的
- 「除外場」は、ROI/回収/運用本数（CAPなど）に直結する重要要素。
- チャット切替で漏れると検証結果の解釈が崩れるため、**ここを正本**として管理し、毎回の引継ぎに必ず含める。

## 現状（初期値）
- 既定は **除外なし**（exclude_jcd = []）。
- 除外を運用に入れる場合は、必ず「理由」「期間」「期待効果（ROI/欠落回避/工数）」を明記し、JSONも更新する。

## 運用ルール（不変）
- 検証・実践の出力には **exclude_jcd を必ず明記**する（空でも「none」と書く）。
- TOP10CAPなど、日次本数制約がある検証は、除外の有無で結果が大きく変わりうるため、比較は必ず同条件で行う。

## 除外リスト（運用）
- updated: 2026-01-06
- source_of_truth: `C:\work\boatrace\config\exclusions.json`
- excluded_jcd: `03,06,07,08,11,12,13,14,16,18,19,20,21,23,24`（15場）

### 根拠（直近の確定）
- 固定窓（2025-10-08..2025-12-30）で CAP10+EXCL10 v2 の what-if を実施し、Core5（+13,16,19,21,24）を本採用。
  - core3（追加: 19,21,24） ROI=1.640620（invest=8.23M / return=13.5023M）
  - core5（追加: 19,21,24,13,16） ROI=1.693739（invest=8.13M / return=13.7701M）※採用
- 本採用後に `run_candidate_cap10_excl10.ps1` で ROI=1.693739 が再現（key_overlap_rate=1.0000）。

### 追加検証（ローリング窓 / 2026-01-06 実施）
- payouts_fixed: `C:\work\boatrace\runs\payouts_all_2025-10-02_2025-12-30_MERGED_keynorm.csv`
- 窓別ROI（core3=Core5から{13,16}を外した比較対象 / core5=現行運用）:
  - W1_30d（2025-10-08..2025-11-06）: core3=2.11044 / core5=2.11044（同等）
  - W2_30d（2025-11-07..2025-12-06）: core3=1.31322 / core5=1.30454（core3僅差）
  - W12_60d（2025-10-08..2025-12-06）: core3=1.71048 / core5=1.70612（core3僅差）
  - W3_30d（2025-12-01..2025-12-30）: core3=1.21756 / core5=1.35425（core5明確に優位）
- 結論：**直近30d（W3）で core5 が明確に勝つ**ため、運用は core5（現行 `exclusions.json`）を継続採用する。

### 除外対象一覧（運用ON）
| jcd | 場 | 理由 | 適用レンジ | 状態 |
|---:|---|---|---|---|
| 3 | 江戸川 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 6 | 浜名湖 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 7 | 蒲郡 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 8 | 常滑 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 11 | びわこ | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 12 | 住之江 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 13 | 尼崎 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 14 | 鳴門 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 16 | 児島 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 18 | 徳山 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 19 | 下関 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 20 | 若松 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 21 | 芦屋 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 23 | 唐津 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |
| 24 | 大村 | 運用判断（ROI/回収の改善目的） | 2025-10-08..（暫定） | 運用ON |

# 重要要素（未採用でも引継ぎ必須） 正本

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


- docs/UPLOAD_MINSET_GUIDE.md：ローカル詰まり時の「CSVアップ→AI加工」minset手順

## 未完了（次チャットへ）

- [TODO / 次チャット] `cap10_select_conf_top10_v3.py` の `columns overlap but no suffix specified: ['date','jcd','race_no']` を根治
  - 原因：pandas merge/join でキー列が重複（suffix未指定）
  - 対策：join前に右側の `date/jcd/race_no` を drop する or suffix 付与
  - ERROR_COOKBOOK に「この表現のまま」追記して再発時に迷子にならないようにする


## 90D検証の出力ルール（再発防止）
- 90D結果を貼るときは、最上段で **期間 Expected/Actual と一致判定（OK/NG）** を必ず明記。
- 「比較」欄は **BL/BT×Baseline/Candidate 対比表** を必須化し、`CAP / 除外場（運用制約）= OFF/ON` で表示。
