# -*- coding: utf-8 -*-
"""
salvage_cap10_core5_from_tickets.py

Fallback builder to guarantee C-phase goal artifacts exist even if upstream runner fails.
Input: a tickets_long csv that contains at least [date, jcd, race_no] and a confidence-like column.
Output into run dir:
  - CAP10_core5_races.csv (race-level top-N by conf)
  - CAP10_core5_tickets_long.csv (filtered to selected races)
  - CAP10_core5_meta.json

This script is intentionally dependency-light and tolerant of column name variations.
"""
import argparse, json, os, re
import pandas as pd

CONF_CANDS = ["tier_conf","conf","race_conf","score","race_score","conf_score","p_win","p_top1","p_top2","p_top3"]
TIER_CANDS = ["tier","rank","grade","tier_label","sa","SA","tier_sa"]

JCD_TO_TRACK = {
  1:"桐生",2:"戸田",3:"江戸川",4:"平和島",5:"多摩川",6:"浜名湖",7:"蒲郡",8:"常滑",9:"津",10:"三国",11:"びわこ",12:"住之江",
  13:"尼崎",14:"鳴門",15:"丸亀",16:"児島",17:"宮島",18:"徳山",19:"下関",20:"若松",21:"芦屋",22:"福岡",23:"唐津",24:"大村"
}

def read_csv_any(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig","cp932","utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    return pd.read_csv(path, encoding="utf-8", errors="ignore", low_memory=False)

def pick_col(df, cands):
    for c in cands:
        if c in df.columns:
            return c
    # try fuzzy
    cols = {c.lower():c for c in df.columns}
    for c in cands:
        if c.lower() in cols:
            return cols[c.lower()]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True, help="tickets_long*.csv path")
    ap.add_argument("--run", required=True, help="RunDir output")
    ap.add_argument("--cap", type=int, default=10)
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (optional filter)")
    args = ap.parse_args()

    if not os.path.exists(args.tickets):
        raise SystemExit(f"NG: tickets not found: {args.tickets}")

    os.makedirs(args.run, exist_ok=True)

    df = read_csv_any(args.tickets)
    need = {"date","jcd","race_no"}
    if not need.issubset(df.columns):
        raise SystemExit(f"NG: tickets missing keys {need}. cols={list(df.columns)[:80]}")

    conf_col = pick_col(df, CONF_CANDS)
    if conf_col is None:
        raise SystemExit(f"NG: conf column not found. tried={CONF_CANDS}. cols={list(df.columns)[:120]}")

    tier_col = pick_col(df, TIER_CANDS)

    df["date"] = df["date"].astype(str).str.strip()
    df["jcd"] = pd.to_numeric(df["jcd"], errors="coerce").astype("Int64")
    df["race_no"] = pd.to_numeric(df["race_no"], errors="coerce").astype("Int64")
    df[conf_col] = pd.to_numeric(df[conf_col], errors="coerce")

    if args.date:
        df = df.loc[df["date"]==args.date].copy()

    # prefer S/A if tier exists and looks like it
    work = df
    if tier_col is not None:
        t = work[tier_col].astype(str).str.upper().str.strip()
        sa = work[t.isin(["S","A"])].copy()
        if not sa.empty:
            work = sa

    # race-level
    grp = work.groupby(["date","jcd","race_no"], dropna=False)[conf_col].max().reset_index()
    grp = grp.rename(columns={conf_col:"conf"})
    grp["track_name"] = grp["jcd"].map(lambda x: JCD_TO_TRACK.get(int(x)) if pd.notna(x) else "")
    grp = grp.sort_values(["conf"], ascending=False).head(args.cap)

    if grp.empty:
        raise SystemExit("NG: selection empty after filtering")

    sel = grp[["date","jcd","race_no"]].drop_duplicates()
    df2 = df.merge(sel, on=["date","jcd","race_no"], how="inner")

    out_races = os.path.join(args.run, "CAP10_core5_races.csv")
    out_tickets = os.path.join(args.run, "CAP10_core5_tickets_long.csv")
    out_meta = os.path.join(args.run, "CAP10_core5_meta.json")

    grp.to_csv(out_races, index=False, encoding="utf-8-sig")
    df2.to_csv(out_tickets, index=False, encoding="utf-8-sig")

    meta = {
        "method": "fallback_salvage_from_tickets_long",
        "cap": args.cap,
        "date_filter": args.date,
        "inputs": {"tickets": os.path.abspath(args.tickets), "conf_col": conf_col, "tier_col": tier_col},
        "outputs": {"races": os.path.abspath(out_races), "tickets_long": os.path.abspath(out_tickets)}
    }
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("OK")
    print("SRC_TICKETS =", args.tickets)
    print("CONF_COL =", conf_col)
    print("OUT_RACES =", out_races)
    print("OUT_TICKETS =", out_tickets)
    print("OUT_META =", out_meta)

if __name__ == "__main__":
    main()
