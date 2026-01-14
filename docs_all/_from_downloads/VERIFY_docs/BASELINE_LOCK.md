# Baseline manifest (lock)

This file is a **source-of-truth lock** for the current operational baseline worldline.

- Baseline name: CAP10_EXCL_BASELINE_2025-12-03_2025-12-30_S_ONLY_DROP_SKIP_NO_S3F
- Tickets: `C:\work\boatrace\runs\CAP10_EXCL_20251203_1230_tickets_long_racelevel_DROP_SKIP_NO_S3F.csv`
- Payouts: `C:\work\boatrace\runs\payouts_all_2025-10-02_2025-12-30_MERGED_keynorm.csv`

Expected (confirmed):
- tickets date_range: 2025-12-03 .. 2025-12-30
- tiers: S
- ROI: invest=1080000 return=991400 roi=0.917963

Use `verify_baseline.ps1` to re-check reproducibility at any time.

### ベースライン変更ポリシー（重要）
- 実践フロー・30d/90d検証の **ベースラインに関わる** スクリプト/バッチを **新規作成・更新** する場合は、必ずユーザの **明示的な合意** を得てから実施する。
- ベースライン関連スクリプト/バッチを **チャット内で実行・再現** したい場合、効率/精度が大幅に上がる時に限り、ユーザへ **ファイルのアップロード** を提案してから進める。
- 同一タスクでエラーが連続する場合は、早めに「🟡CSVアップ→AI側で加工」へ切替し、エラーラリーを抑制する。
