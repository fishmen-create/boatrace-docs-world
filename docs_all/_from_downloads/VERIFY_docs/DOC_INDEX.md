#TEST_ABC123
# DOC_INDEX（文書インデックス）正本
最終更新: 2026-01-09

このファイルは「迷子防止」のための**起点（入口）**です。  
困ったらまずここ→該当ドキュメントへ飛んでください。

---

## 1) 今すぐC（Check準備）を完走したい（運用）
- **入口（最短）**：`C_CHECK_TIGERBOOK.md`  
  - C開始条件 / 入力の用意（誰が・いつ・何を・どうやって） / C-2〜C-5 / 既知エラーの対処
- **C-5（締切表示）正フォーマット**：
  - 列：`締切(JST) | 場R | ランク(S/A) | ランキング | conf`
  - `場R` は「場名+R」を結合（例：`三国2R` / `丸亀10R`）して余白を減らす
  - **締切昇順**で表示
  - 表示は **UI表示に依存せず、必ずチャット本文にテキスト表を貼る**（CSVも併記）
  - 正ファイル名：`C_selected_races_deadline_sorted_YYYY-MM-DD_with_tier.csv`

関連：
- `RUNBOOK_PRACTICE.md`（PDCA全体。Cの詳細は虎の巻へ）
- `SPEC_FIXED.md`（固定仕様。閾値・S/A運用ルール）

---

## 2) エラーが出た（まず引ける場所）
- **入口**：`ERROR_COOKBOOK_BOATRACE_CAP10.md`  
  - 典型エラー → 原因 → 1行対処 → 次に貼るべきログ

C（Check準備）に直結する代表例：
- features collector の `--b-dir required`
- selector の `columns overlap but no suffix specified`
- `conf列が無い` / `列名揺れ`

---

## 3) 仕様が勝手に変わっていないか確認したい
- **入口**：`SPEC_FIXED.md`
- 次点：`IMPORTANT_ELEMENTS.md`（絶対に落とせない要素一覧）

---

## 4) 除外場・例外（config）を見直したい
- **入口**：`TRACK_EXCLUSIONS.md`
- 関連：`CANDIDATE_LOCK_CAP10_EXCL10.md` / `CAP10_SELECTION_ORDER_LOCK.md`

---

## 5) チャット切替・引継ぎが重い/漏れる
- **入口**：`HANDOVER.md` / `HANDOVER_HARDENING.md`
- 関連：`COMMUNICATION_RULES.md` / `USER_TENDENCIES.md`

---

## 6) 「🟡アップ→AI加工」最小セットで回したい
- **入口**：`UPLOAD_MINSET_GUIDE.md`

---

## 7) 90D検証（検証フェーズ）
- **入口（守るルール）**：`RUNBOOK_90D.md`  
  - WORLD（BL/BT）分離、入口チェック、実行順、禁止事項、出口定義、検証条件セット
  - 反映フェーズに渡す「改修スコープテンプレ（ユーザ意思決定・切替耐性）」は **RUNBOOK_90D.md の 6-A**
- **入口（迷った時の虎の巻）**：`BR_90D_TIGERBOOK.md`  
  - 章立て（器）＋典型トラブル／入口要点（T_end/T_start・日付フォーマット・payout疎通）＋意思決定ルール（数値→判定→所感）

（参考：旧版ガイド）
- `BR_90D_VERIFY_GUIDE_FINAL_20260111_v26_DATEFORMAT.md` ほか（過去の統合元／必要時のみ参照）

