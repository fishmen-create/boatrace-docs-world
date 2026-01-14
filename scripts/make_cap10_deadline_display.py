# -*- coding: utf-8 -*-
"""make_cap10_deadline_display.py

Purpose:
  Create "display goal" artifacts for C-phase:
    - CAP10_core5_races_deadline_sorted.csv (sorted by deadline time)
    - CAP10_core5_deadline_list.md (markdown table)

Spec-aligned behavior:
  - Attach deadline_time using inputs that are available on the day.
  - Priority:
      0) race_summary*.csv found under RunDir (= C_OUT_FIXED_YYYY-MM-DD)
      1) runs/C_OUT_<date>_*/ *race_summary*.csv
      2) (optional) all_k_results*.csv (only if --allow-allk)

Notes:
  - This script is for DISPLAY only; CAP10 selection order is conf-based.
  - Display is sorted by deadline_time (HH:MM).
"""

import argparse
import glob
import os
import re
from typing import Optional, Tuple

import pandas as pd

# jcd -> Japanese track name (for display only)
JCD_TO_TRACK = {
    1: "桐生", 2: "戸田", 3: "江戸川", 4: "平和島", 5: "多摩川", 6: "浜名湖",
    7: "蒲郡", 8: "常滑", 9: "津", 10: "三国", 11: "びわこ", 12: "住之江",
    13: "尼崎", 14: "鳴門", 15: "丸亀", 16: "児島", 17: "宮島", 18: "徳山",
    19: "下関", 20: "若松", 21: "芦屋", 22: "福岡", 23: "唐津", 24: "大村",
}
TRACK_TO_JCD = {v: k for k, v in JCD_TO_TRACK.items()}

TIME_COL_CANDIDATES = [
    "deadline_time", "締切", "締切時刻", "締め切り", "〆切", "cutoff", "deadline",
    "start_time", "発走", "発走時刻",
]


def read_csv_any(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    return pd.read_csv(path, encoding="utf-8", errors="ignore", low_memory=False)


def norm_date(s: str) -> str:
    return str(s).strip()


def parse_hhmm(x) -> Optional[int]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def pick_time_col(df: pd.DataFrame) -> Optional[str]:
    for c in TIME_COL_CANDIDATES:
        if c in df.columns:
            return c
    return None


def _to_deadline_table(df: pd.DataFrame, src: str) -> pd.DataFrame:
    tc = pick_time_col(df)
    if tc is None:
        raise SystemExit(f"NG: deadline source found but time col not found: {src}\ncols={list(df.columns)}")

    # normalize keys
    if {"date", "jcd", "race_no"}.issubset(df.columns):
        out = df[["date", "jcd", "race_no", tc]].copy()
        out = out.rename(columns={tc: "deadline_time"})
        return out

    # sometimes: date + track_name + race_no
    if {"date", "track_name", "race_no"}.issubset(df.columns):
        out = df[["date", "track_name", "race_no", tc]].copy()
        out["jcd"] = out["track_name"].map(lambda x: TRACK_TO_JCD.get(str(x).strip(), None))
        out = out.drop(columns=["track_name"]).rename(columns={tc: "deadline_time"})
        return out

    # sometimes: date + jyo + race_no
    if {"date", "jyo", "race_no"}.issubset(df.columns):
        out = df[["date", "jyo", "race_no", tc]].copy()
        out = out.rename(columns={"jyo": "jcd", tc: "deadline_time"})
        return out

    raise SystemExit(f"NG: deadline source keys not found: {src}\ncols={list(df.columns)}")


def find_local_race_summary(run_dir: str) -> Optional[str]:
    patterns = [
        os.path.join(run_dir, "race_summary*.csv"),
        os.path.join(run_dir, "*race_summary*.csv"),
        os.path.join(run_dir, "race_summary*.CSV"),
        os.path.join(run_dir, "*race_summary*.CSV"),
    ]
    files = []
    for p in patterns:
        files += glob.glob(p)
    # also allow explicit filename used in some workflows
    explicit = os.path.join(run_dir, "race_summary_races.csv")
    if os.path.exists(explicit):
        files.append(explicit)
    files = sorted(set(files), key=lambda x: os.path.getmtime(x))
    return files[-1] if files else None


def find_c_out_race_summary(root: str, date: str) -> Optional[str]:
    patterns = [
        os.path.join(root, "runs", f"C_OUT_{date}_*", "*race_summary*.csv"),
        os.path.join(root, "runs", f"C_OUT_{date}_*", "*race_summary*.CSV"),
        os.path.join(root, "runs", f"C_OUT_{date}_*", "*Race_Summary*.csv"),
    ]
    files = []
    for p in patterns:
        files += glob.glob(p)
    files = sorted(set(files), key=lambda x: os.path.getmtime(x))
    return files[-1] if files else None


def find_latest_allk(root: str) -> Optional[str]:
    cands = sorted(glob.glob(os.path.join(root, "all_k_results*.csv")))
    return cands[-1] if cands else None


def build_deadline_table(root: str, date: str, run_dir: str, allow_allk: bool) -> Tuple[pd.DataFrame, str]:
    tried = []

    # Priority 0: RunDir local race_summary
    rs0 = find_local_race_summary(run_dir)
    if rs0:
        tried.append(("run_dir_race_summary", rs0))
        df0 = read_csv_any(rs0)
        return _to_deadline_table(df0, rs0), f"run_dir_race_summary={rs0}"

    # Priority 1: runs/C_OUT_<date>_*/race_summary
    rs1 = find_c_out_race_summary(root, date)
    if rs1:
        tried.append(("c_out_race_summary", rs1))
        df1 = read_csv_any(rs1)
        return _to_deadline_table(df1, rs1), f"c_out_race_summary={rs1}"

    # Priority 2 (optional): all_k_results
    if allow_allk:
        allk = find_latest_allk(root)
        if allk:
            tried.append(("all_k_results", allk))
            dfk = read_csv_any(allk)
            if not {"date", "jcd", "race_no"}.issubset(dfk.columns):
                raise SystemExit(f"NG: all_k_results keys not found: {allk}\ncols={list(dfk.columns)}")
            tc = pick_time_col(dfk)
            if tc is None:
                raise SystemExit(f"NG: all_k_results found but time col not found: {allk}\ncols={list(dfk.columns)}")
            dfk["date"] = dfk["date"].map(norm_date)
            out = dfk.loc[dfk["date"] == date, ["date", "jcd", "race_no", tc]].copy()
            out = out.rename(columns={tc: "deadline_time"})
            if out.empty:
                raise SystemExit(f"NG: all_k_results exists but has no rows for date={date}: {allk}")
            return out, f"all_k_results={allk}"

    raise SystemExit(
        "NG: deadline source not found. tried: "
        "RunDir/*race_summary*.csv, runs/C_OUT_<date>_*/race_summary" +
        (", all_k_results*.csv" if allow_allk else "") +
        f"\nRunDir={run_dir}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--races", required=True, help="CAP10_core5_races.csv path")
    ap.add_argument("--outdir", required=True, help="output dir (usually C_OUT_FIXED_YYYY-MM-DD)")
    ap.add_argument("--root", default=r"C:\\work\\boatrace", help="project root")
    ap.add_argument("--allow-allk", action="store_true", help="allow fallback to all_k_results*.csv")
    args = ap.parse_args()

    date = args.date
    root = args.root
    run_dir = args.outdir

    races_path = args.races
    if not os.path.exists(races_path):
        raise SystemExit(f"NG: races csv not found: {races_path}")

    races = read_csv_any(races_path)
    required = {"date", "jcd", "race_no"}
    if not required.issubset(races.columns):
        raise SystemExit(f"NG: races csv missing keys {required}. cols={list(races.columns)}")

    # normalize
    races["date"] = races["date"].map(norm_date)
    races["jcd"] = pd.to_numeric(races["jcd"], errors="coerce").astype("Int64")
    races["race_no"] = pd.to_numeric(races["race_no"], errors="coerce").astype("Int64")

    deadline, src = build_deadline_table(root, date, run_dir, allow_allk=args.allow_allk)
    deadline["date"] = deadline["date"].map(norm_date)
    deadline["jcd"] = pd.to_numeric(deadline["jcd"], errors="coerce").astype("Int64")
    deadline["race_no"] = pd.to_numeric(deadline["race_no"], errors="coerce").astype("Int64")

    merged = races.merge(deadline[["date", "jcd", "race_no", "deadline_time"]],
                         on=["date", "jcd", "race_no"], how="left")

    if "track_name" not in merged.columns:
        merged["track_name"] = merged["jcd"].map(lambda x: JCD_TO_TRACK.get(int(x)) if pd.notna(x) else "")

    if merged["deadline_time"].isna().all():
        raise SystemExit(f"NG: deadline_time could not be attached for date={date}. source={src}")

    merged["_m"] = merged["deadline_time"].map(parse_hhmm)
    if merged["_m"].isna().all():
        raise SystemExit(
            f"NG: deadline_time exists but not HH:MM. sample={merged['deadline_time'].head(5).tolist()} source={src}"
        )

    merged = merged.sort_values(["_m"], ascending=True).drop(columns=["_m"])

    os.makedirs(args.outdir, exist_ok=True)
    out_csv = os.path.join(args.outdir, "CAP10_core5_races_deadline_sorted.csv")
    merged.to_csv(out_csv, index=False, encoding="utf-8-sig")

    cols = ["deadline_time", "track_name", "race_no"]
    for c in ["tier", "conf", "axis1", "axis2"]:
        if c in merged.columns:
            cols.append(c)

    md = os.path.join(args.outdir, "CAP10_core5_deadline_list.md")
    header = f"# {date} CAP10（締切が早い順・表示用ソート）\n\n"
    header += "※ CAP10の選定自体はconf順で確定済み → **表示だけ締切順**です\n\n"
    header += "| " + " | ".join(cols) + " |\n"
    header += "| " + " | ".join(["---"] * len(cols)) + " |\n"

    def fmt(v):
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            return f"{v:.3f}".rstrip("0").rstrip(".")
        return str(v)

    for _, r in merged[cols].iterrows():
        header += "| " + " | ".join(fmt(r[c]) for c in cols) + " |\n"

    with open(md, "w", encoding="utf-8") as f:
        f.write(header)

    print("OK")
    print("SRC =", src)
    print("OUT_CSV =", out_csv)
    print("OUT_MD  =", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
