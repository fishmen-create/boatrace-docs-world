
# boatrace_backtest_v12_prune_configurable_s087_alltracks_FIXED.py
# FIXED: mode split (analysis / operation), CAP10 & EXCL guard, date normalization

import argparse
from datetime import datetime

def normalize_date(s: str) -> str:
    if "-" in s:
        return s
    return datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["analysis", "operation"], required=True)
    parser.add_argument("--date-from", required=True)
    parser.add_argument("--date-to", required=True)
    parser.add_argument("--daily-cap", type=int, default=None)
    parser.add_argument("--exclude-jcd", nargs="*", default=None)
    parser.add_argument("--daily-cap-priority", default="conf")

    args = parser.parse_args()

    args.date_from = normalize_date(args.date_from)
    args.date_to   = normalize_date(args.date_to)

    if args.mode == "analysis":
        if args.daily_cap is not None or args.exclude_jcd:
            raise ValueError(
                "[CONFIG ERROR] analysis mode では CAP10 / exclude_jcd は使用できません"
            )

    print(f"[INFO] backtest run mode = {args.mode}")
    print(f"[INFO] date range = {args.date_from} .. {args.date_to}")
    print("[OK] script loaded with enforced mode separation")

if __name__ == "__main__":
    main()
