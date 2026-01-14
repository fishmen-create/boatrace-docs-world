import pandas as pd
import sys
from pathlib import Path

DATE = sys.argv[1]  # YYYY-MM-DD
RUNS = Path(r"C:\work\boatrace\runs")
OUT  = RUNS / f"C_OUT_FIXED_{DATE}"
OUT.mkdir(parents=True, exist_ok=True)

report = RUNS / "backtest_alltracks_2025-10-13_2026-01-10_v12prune_s087_baseline_report.csv"
tlong  = RUNS / "backtest_alltracks_2025-10-13_2026-01-10_v12prune_s087_baseline_tickets_long.csv"

if not report.exists():
    raise SystemExit(f"report not found: {report}")
if not tlong.exists():
    raise SystemExit(f"tickets_long not found: {tlong}")

R = pd.read_csv(report, encoding="utf-8-sig", low_memory=False)
T = pd.read_csv(tlong,  encoding="utf-8-sig", low_memory=False)

if "date" not in R.columns:
    raise SystemExit("report has no 'date' column")
if "date" not in T.columns:
    raise SystemExit("tickets_long has no 'date' column")

R = R[R["date"].astype(str) == DATE]
T = T[T["date"].astype(str) == DATE]

# run_C_out_core5_cap10.ps1 は *races*.csv を探すので、名前に races を入れる
r_out = OUT / "race_summary_races.csv"
t_out = OUT / "tickets_long.csv"

R.to_csv(r_out, index=False, encoding="utf-8-sig")
T.to_csv(t_out, index=False, encoding="utf-8-sig")

print("OK sliced:", len(R), "races,", len(T), "tickets")
print("WROTE:", r_out)
print("WROTE:", t_out)
