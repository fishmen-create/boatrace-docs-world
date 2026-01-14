## K（mbrace Kファイル）と b-only 運用（当日予想）

### 結論
- **当日朝の予想生成では `--b-only` が正（デフォルト）**。
- K（mbrace Kファイル）は「日別競走成績＝結果データ」なので、**当日Dのレースが未確定の時間帯には存在しない/取得できない**。
- よって、当日朝フローで「Kに当日Dの行が無い」ことは異常ではなく仕様。

### 理由（download_mbrace_k.py の動作）
- `download_mbrace_k.py` は mbrace のURLテンプレート `.../K/{ym}/k{yymmdd}.lzh` から **日別の kYYMMDD.lzh を取得**するだけのスクリプト。
- **404 の場合は「その日はファイル無し」と判断してスキップ**する（= 未来日や未確定日は取得できない）。  
  → つまり「前日夜に回して当日Dの行を作る」仕組みではない。

### 使うスクリプト（当日朝 / 予想用）
- Bファイル展開：`prepare_b_files_v2.py`
- 公式features収集（当日予想は b-only がデフォルト）：`collect_boatrace_official_features_bonly_v2.py --b-only ...`
- dedup（v1.2必須）：`dedup_official_features.py`

### K（all_k_results.csv / download_mbrace_k.py）は何のために使う？
- **主用途：検証（True90 / backtest / 翌日以降の集計）**
- 当日DのKが揃うのは「当日終了後〜翌日以降」なので、K更新はそのタイミングで行う。
- 当日朝の予想フローは、Kの有無で止めない（止めると日次運用が破綻する）。
