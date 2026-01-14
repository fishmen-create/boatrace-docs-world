# C（Check準備）虎の巻（正本）
最終更新: 2026-01-09
対象: 競艇予想 v1.2（運用側） / 「迷いなくCを完走する」ための1枚

---

## 0. 目的（Cフェーズのゴール）
**予測精度を落とさず**、当日（D）の締切15分前に迷いなく判断できるように、  
**「選定レース一覧（Top10）」を画面表示**し、同内容をCSVとして保存する。

- ゴール出力（正本）
  - `C:\work\boatrace\runs\C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv`
- 表示（最低限）
  - `date, jcd, race_no, conf, rank`
- 表示（追加：希望）
  - 上記に **締切時刻** を付与し、**締切昇順**に並べて表示（C-5）

---

## 1. C開始条件（止める/止めない）
### 止める（C開始に必須）
- **fan**（選手成績）
- **Bファイル**（当日分が `b_files` にある）
- **official_features（当日分）** が取得できること  
  - かつ **dedup済み**であること

### 止めない（C開始に不要）
- all_k_results の**最新化**
- payout の**最新化**（ROI計算はCの必須ではない）

> ただし実装都合で collector が `--all-k-csv` を要求する場合があるため、  
> **all_k_results*.csv は「存在すればOK（最新化は不要）」**とする。

---

## 2. 役割分担（誰が/いつ/何を/どうやって）
### ユーザ（ローカル）— C-2〜C-4の実行主体
- **いつ**：当日朝〜（締切15分前までにC-5まで終わっていればOK）
- **何を**：C-2（features準備）→ C-3（予測生成）→ C-4（Top10選定）

### AI（チャット）— C-5（締切表示）主体
- **いつ**：C-4完了後（締切15分前の判断に間に合うタイミング）
- **何を**：`C_selected_races.csv` に締切時刻を付与し、締切昇順で表示・CSV化
- **どうやって**：ユーザが `C_selected_races.csv` をアップロード → AIがWebから締切を補完

---

## 3. C-2（入力準備：Bファイル整理 → official_features取得 → dedup）
### 入力
- Bファイル（`C:\work\boatrace\b_files` に当日分が揃っている）
- fan（既存運用どおり）
- all_k_results*.csv（存在すればOK。最新化は不要）

### Bファイルはどこで使う？
- BはC-3の直接入力ではないが、**C-2のfeatures取得で日付・対象レースを確定するために使用**する（`--b-dir`）。
- そのため、I/O定義上は **C-2の必須入力**として扱う。

### 出力（C-2成果物）
- `C:\work\boatrace\runs\official_features_alltracks_YYYY-MM-DD_YYYY-MM-DD_dedup.csv`

### 正とするスクリプト（この3つで合っている）
- `prepare_b_files_v2.py`
- `collect_boatrace_official_features_bonly_v2.py`
- `dedup_official_features.py`

---

## 4. C-3（C本体：暫定予想生成）
### 入力
- C-2成果物：`official_features_alltracks_..._dedup.csv`

### 正とするスクリプト
- `C:\work\boatrace\scripts\run_C_out.ps1`

### 出力（runs直下に生成）
- `C_OUT_YYYY-MM-DD_*_tickets_long.csv`
- `C_OUT_YYYY-MM-DD_*_report.csv`
- `C_OUT_YYYY-MM-DD_*_C_race_summary.csv`

---

## 5. C-4（選定：Top10抽出 → C_selected_races.csv）
### 前提（確定事項）
- `tickets_long.csv` に **conf列が無い**
- `report.csv` に **conf列がある**
→ **C-4で tickets に conf を付与**してから selector を実行する。

### 中間出力（固定）
- `C_OUT_FIXED_YYYY-MM-DD\C_tickets_long_with_conf.csv`

### 最終出力（固定）
- `C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv`
- `C_OUT_FIXED_YYYY-MM-DD\C_cap10_tickets.csv`

### 正とするスクリプト
- selector：`C:\work\boatrace\cap10_select_conf_top10_v3.py`
  - 既知バグ/対策（2026-01-09実績）
    - `ValueError: columns overlap but no suffix specified: ['date','jcd','race_no']`
    - 対策：join前に右側から `['date','jcd','race_no']` を drop（パッチ適用）

---

## 6. C-5（表示補助：締切時刻の付与と昇順ソート）

### 目的（Cのゴール：画面表示）
- C-4で作成した `C_selected_races.csv`（CAP10選定結果）に **締切時刻（JST）**を付与して、
  **締切昇順**の一覧を **チャット本文にテキスト表で表示**する（UI表示は使わない）
- 併せてCSVを出力する（運用チャット/後工程へ渡しやすくする）

### 入力（誰が/いつ/どうやって用意）
- **誰が**：ユーザ（ローカルでC-4まで完走して生成）
- **いつ**：当日（締切15分前より前）
- **何を**：`C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv`
  - これは C-4（CAP10選定）で作られる成果物（C-5側で新規作成しない）
- **どうやって**：C-4完走後に runs 配下の `C_OUT_FIXED_YYYY-MM-DD` を確認して取得

### 出力（正：ファイル）
- `C_OUT_FIXED_YYYY-MM-DD\C_selected_races_deadline_sorted_YYYY-MM-DD_with_tier.csv`

### 表示フォーマット（正：チャットに貼る）
列：`締切(JST) | 場R | ランク(S/A) | ランキング | conf`
- `場R`：場名とRを結合（例：`三国2R` / `丸亀10R`）
- `ランク(S/A)`：`conf` の閾値で付与（S>=0.87, A=0.60–0.87）
- `ランキング`：CAP10内の順位（1〜10）
- **締切昇順**で並べる

### 重要（形骸化/迷子防止）
- C-5は“表示補助”だが、**運用の入口（締切順の意思決定）**なので
  **必ずこの表を貼る＋CSVも残す**こと（UI表示の見えない事故を回避）
※精度に影響しない表示補助。**C-1〜C-4の完走が最優先**。

### 入力
- `C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv`

### 実行主体（当面の正）
- **AI（チャット）**がWebから締切を補完（過去運用どおり）

### 出力
- 画面表示：締切昇順の一覧
- CSV：`C_selected_races_deadline_sorted.csv`

---

## 7. C完走の判定（これが揃えばOK）
- `C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv` が存在し、Top10になっている
- （希望）C-5で締切昇順の一覧が表示できる

---

## 8. 既知の詰まりポイント（原因→対策）
- **C-4で conf が無い**
  - 原因：tickets_longにconf列が無い
  - 対策：report.conf を tickets に付与して `C_tickets_long_with_conf.csv` を作ってから selector
- **selector が columns overlap で落ちる**
  - 原因：selectorのjoin実装バグ
  - 対策：`date/jcd/race_no` を右側からdropしてjoin（パッチ）
- **payout更新が無い期間でもCを回したい**
  - 設計：Cは payout不要。ROIは検証/改善側へ分離

---

# 付録A：入力ファイルの用意（ユーザ作業・最小コマンド集）

## A-1) Bファイルを `b_files` に揃える（Downloads→b_files）
```powershell
cd C:\work\boatrace
python .\prepare_b_files_v2.py --src "$env:USERPROFILE\Downloads" --dst "C:\work\boatrace\b_files"
```

確認（当日分があるか）：
```powershell
dir "C:\work\boatrace\b_files\B*.TXT" | sort LastWriteTime -Desc | select -First 10 Name,LastWriteTime,Length
```

## A-2) official_features を取得（b-only）→ dedup
※ `all_k_results*.csv` は「存在すればOK（最新化は不要）」  
```powershell
# 例：最も新しい all_k_results*.csv を拾う（存在確認）
dir C:\work\boatrace\all_k_results*.csv | sort LastWriteTime -Desc | select -First 1
```

取得：
```powershell
$DATE="YYYY-MM-DD"
$ALLK=(dir C:\work\boatrace\all_k_results*.csv | sort LastWriteTime -Desc | select -First 1).FullName
$RAW="C:\work\boatrace\runs\official_features_alltracks_${DATE}_${DATE}.csv"
$DEDUP="C:\work\boatrace\runs\official_features_alltracks_${DATE}_${DATE}_dedup.csv"

python .\collect_boatrace_official_features_bonly_v2.py --all-k-csv "$ALLK" --b-dir "C:\work\boatrace\b_files" --date-from $DATE --date-to $DATE --output "$RAW" --b-only
python .\dedup_official_features.py --input "$RAW" --output "$DEDUP"
```

確認：
```powershell
Test-Path "$DEDUP"
```

---

# 付録B：C-5（締切表示）をAIに依頼する時に渡すもの
- `C_OUT_FIXED_YYYY-MM-DD\C_selected_races.csv`（これ1つ）
- 追加であると良い：当日の「場名/場コード対応表」が必要ならAI側で補完する

---

# 付録C：関連ドキュメント（迷子防止）
- 入口：`DOC_INDEX.md`
- PDCA全体：`RUNBOOK_PRACTICE.md`
- 固定仕様：`SPEC_FIXED.md`
- 典型エラー：`ERROR_COOKBOOK_BOATRACE_CAP10.md`
