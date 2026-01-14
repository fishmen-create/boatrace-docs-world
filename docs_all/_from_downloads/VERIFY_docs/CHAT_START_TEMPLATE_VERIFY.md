今日は検証フェーズです。最上位ゴールは長期ROI最大化（全場・再現性）。
検証テーマ：XXXX
比較対象：baseline vs candidate（期間：YYYY-MM-DD〜YYYY-MM-DD）
評価指標：ROI（30d/90d/rolling）、件数、S/A精度、再現性
参照：Projectの 00_CORE/DOC_INDEX.md → 20_VERIFY/（RUNBOOK/LOCK/LEDGER）→ 40_TROUBLE/ERROR_COOKBOOK
結論：採用/不採用、反映差分（SPEC/RUNBOOK/LEDGER更新）を明確にする。

---
## 追加（必須）：WORLDメタ（BL/BT）
- このチャット/検証のWORLDを冒頭で宣言：`WORLD=BL(mode=analysis)` or `WORLD=BT(mode=operation)`
- 出力CSV/summaryにも同じ1行メタを残す（window/CAP/EXCL/source_of_truth）。

