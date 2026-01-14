# -*- coding: utf-8 -*-
"""
make_excl10p2_from_summary_bytrack.py

Purpose:
  Build an "EXCL10P2" candidate exclusion list from an *analysis-mode* (BL_*) summary_bytrack.csv.

Design (assumptions; edit if your project defines EXCL10P2 differently):
  - Use analysis-mode per-track ROI as the primary ranking signal (lower ROI => exclude).
  - Ignore tracks with too little sample to avoid noise (min_inv_yen threshold).
  - Select worst N tracks by ROI. EXCL10P2 = 12 tracks by default (10 + 2).

Inputs:
  --summary-bytrack  : runs/BL_YYYY-MM-DD_YYYY-MM-DD_summary_bytrack.csv
  --out-json         : exclusions_EXCL10P2_candidate.json
Optional:
  --n-exclude        : number of tracks to exclude (default 12)
  --min-inv-yen      : minimum investment per track required to be eligible for ranking (default 3_000_000)
  --mode-tag         : string saved into json meta (default "EXCL10P2_candidate")

Output JSON format:
  {
    "meta": {...},
    "exclude_jcd": [ ... ],
    "rationale": [
        {"rank":1, "jcd":.., "track_name":"..", "roi":.., "inv_sum":.., "ret_sum":.., "n_bet":..},
        ...
    ]
  }
"""
import argparse, json
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-bytrack", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--n-exclude", type=int, default=12)
    ap.add_argument("--min-inv-yen", type=int, default=3_000_000)
    ap.add_argument("--mode-tag", default="EXCL10P2_candidate")
    args = ap.parse_args()

    df = pd.read_csv(args.summary_bytrack)

    # normalize column names expected in our project outputs
    # Common: jcd, track_name, n_bet, inv_sum, ret_sum, roi
    required = {"jcd","track_name","roi","inv_sum","ret_sum"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERR] summary_bytrack missing columns: {sorted(missing)}")

    # Convert numeric
    for c in ["roi","inv_sum","ret_sum","n_bet"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Eligible tracks for ranking
    elig = df.copy()
    elig["eligible"] = (elig["inv_sum"].fillna(0) >= args.min_inv_yen)

    # Rank by ROI (ascending) among eligible
    rank_df = elig[elig["eligible"]].sort_values(["roi","inv_sum"], ascending=[True,False]).copy()
    if len(rank_df) < args.n_exclude:
        print(f"[WARN] eligible tracks ({len(rank_df)}) < n_exclude ({args.n_exclude}). Will exclude all eligible tracks.")
    picked = rank_df.head(args.n_exclude).copy()

    exclude_jcd = [int(x) for x in picked["jcd"].tolist() if pd.notna(x)]

    out = {
        "meta": {
            "mode_tag": args.mode_tag,
            "source_summary_bytrack": args.summary_bytrack,
            "n_exclude": args.n_exclude,
            "min_inv_yen": args.min_inv_yen,
            "note": "Built from analysis-mode BL summary_bytrack ROI ranking (lower ROI excluded)."
        },
        "exclude_jcd": exclude_jcd,
        "rationale": []
    }
    for i, r in enumerate(picked.itertuples(index=False), start=1):
        out["rationale"].append({
            "rank": i,
            "jcd": int(getattr(r,"jcd")),
            "track_name": str(getattr(r,"track_name")),
            "roi": float(getattr(r,"roi")),
            "inv_sum": int(getattr(r,"inv_sum")) if pd.notna(getattr(r,"inv_sum")) else None,
            "ret_sum": int(getattr(r,"ret_sum")) if pd.notna(getattr(r,"ret_sum")) else None,
            "n_bet": int(getattr(r,"n_bet")) if hasattr(r,"n_bet") and pd.notna(getattr(r,"n_bet")) else None,
        })

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("[OK] wrote:", args.out_json)
    print("[OK] exclude_jcd:", exclude_jcd)

if __name__ == "__main__":
    main()
