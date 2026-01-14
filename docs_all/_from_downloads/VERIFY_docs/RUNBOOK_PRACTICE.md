# 実践運用フロー（PDCA/CDCA）正本
## 0. ゴール（全工程共通）
- 目的：全場横断での長期ROI最大化
- 制約：1日5〜15R程度（実践運用の上限）
- 思想：説明可能性＞「当てた/外した物語」


## 0.5 入口（迷子防止）
- C（Check準備）の詳細（誰が/いつ/何を/どうやって）は **`C_CHECK_TIGERBOOK.md` を正**とする。
- エラー時は **`ERROR_COOKBOOK_BOATRACE_CAP10.md`** を最初に参照。
- 文書全体の索引は **`DOC_INDEX.md`**。

## C（Check準備）

### C-5（締切表示：運用の“画面表示”ゴール）
- **入力**：`C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv`（C-4で生成済み）
- **出力**：`C_OUT_FIXED_YYYY-MM-DD\C_selected_races_deadline_sorted_YYYY-MM-DD_with_tier.csv`
- **チャット表示（正）**：締切昇順のテキスト表  
  `締切(JST) | 場R | ランク(S/A) | ランキング | conf`
- UI表示（テーブル）ではなく、**必ず本文に表を貼る**（表示されない事故があったため）前日夜〜当日朝：暫定予想
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


### HIT_LOSS配分（Aのみ・ST条件・60/40）を実行に反映する方法（P0）

core5+CAP10 の tickets_long を確定するタイミングで、下記スクリプトを使って **自動で反映**します。

- 実行（PowerShell 推奨）
  - `powershell -ExecutionPolicy Bypass -File .\scripts\run_C_out_core5_cap10.ps1 -Date YYYY-MM-DD`
- 実行（bat。PowerShellから呼ぶ場合は **&** が必要）
  - `& .\scripts\run_C_out_core5_cap10.bat YYYY-MM-DD`

出力（例: `runs\C_OUT_FIXED_YYYY-MM-DD\` 配下）:
- `CAP10_core5_races.csv`
- `CAP10_core5_tickets_long.csv`
- `CAP10_core5_hitloss_report.csv`（HIT_LOSSが適用されたレース一覧・前後の配分）

※ HIT_LOSSの条件に必要な `official_features_all_*_dedup*.csv` は、`runs` 配下から自動探索します。見つからない場合は `-FeaturesCsv` を明示してください。


## 🟡 CSVアップしてAI側で加工（安全確実）
ローカル環境（ExecutionPolicy / パス / 依存関係 / 列名揺れ）で詰まってエラーラリーになりそうな時は、迷わずこのルートへ切替。

### いつ使う？
- `PSSecurityException`（ps1実行不可）/ `Expand-Archive` 失敗 / パス違い / 同一タスクでエラーが連続する（2回以上）
- 「とにかく **運用の出力（races/tickets_long）を確実に得たい**」が最優先の時

### アップする最小ファイル（minset）
- `runs\C_OUT_*DATE*_*_C_race_summary.csv`（Cフェーズのレース一覧：tier/conf/axis等を含む）
- `runs\C_OUT_*DATE*_*_tickets_long.csv`（Cフェーズの tickets_long）
- `config\exclusions.json`（除外場リスト）
- （必要時）`runs\official_features_all_*DATE*_dedup*.csv`（STランク再計算が必要な場合のみ）

### どうやって特定する？
1) まず `runs\C_OUT_FIXED_YYYY-MM-DD\CAP10_core5_meta.json` があればそれが最短（inputs/outputs が全部載っている）
2) 無ければ `runs` 配下で `C_OUT_YYYY-MM-DD_*` の最新ディレクトリを探す（`Get-ChildItem runs -Directory | Sort-Object LastWriteTime -Desc`）

### 期待するAI出力
- `CAP10_core5_races.csv`
- `CAP10_core5_tickets_long.csv`
- `CAP10_core5_meta.json`（入力・除外・件数のトレーサビリティ）