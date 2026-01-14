#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
c_prep_sanity_check.py
C（準備フェーズ）の成果物（tickets_long / selected_races）が「道しるべとして健全か」を検査するスクリプト。
買い目は出しません（件数・分布・欠落・除外混入の有無だけを出します）。

使い方例:
  python c_prep_sanity_check.py ^
    --tickets  C:\work\boatrace\runs\CAP10_EXCL10P2_tickets_long_20260107_141214.csv ^
    --selected C:\work\boatrace\runs\CAP10_EXCL10P2_selected_races_20260107_141214.csv ^
    --exclude-json C:\work\boatrace\config\exclusions_EXCL10P2_candidate.json

終了コード:
  0 = OK
  2 = NG（selectedがticketsに存在しない / 除外場混入 / 日付不一致 など）
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Set, Tuple

import pandas as pd


def _read_json_allow_bom(path: Path) -> dict:
    raw = path.read_bytes()
    # utf-8-sig は BOM があっても剥がして読める
    s = raw.decode("utf-8-sig", errors="replace")
    return json.loads(s)


def load_excluded_jcd(exclude_json: Path | None) -> Set[int]:
    if exclude_json is None:
        return set()

    data = _read_json_allow_bom(exclude_json)

    # よくある形を順に吸収
    for k in ("excluded_jcd", "exclude_jcd", "excluded", "exclude"):
        if isinstance(data.get(k), list):
            out = set()
            for x in data[k]:
                try:
                    out.add(int(x))
                except Exception:
                    continue
            return out

    if isinstance(data.get("tracks"), list):
        out = set()
        for t in data["tracks"]:
            if isinstance(t, dict) and "jcd" in t:
                try:
                    out.add(int(t["jcd"]))
                except Exception:
                    pass
        return out

    return set()


def norm_jcd(v) -> int:
    try:
        return int(v)
    except Exception:
        s = str(v).strip()
        s2 = s.lstrip("0")
        return int(s2 or "0")


def keys(df: pd.DataFrame) -> Set[Tuple[str, int, int]]:
    # (date, jcd, race_no)
    return set(
        zip(
            df["date"].astype(str),
            df["jcd_int"].astype(int),
            df["race_no"].astype(int),
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True, help="CAP/除外後 tickets_long.csv")
    ap.add_argument("--selected", required=True, help="CAP/除外後 selected_races.csv")
    ap.add_argument("--exclude-json", default=None, help="exclusions*.json（任意。指定すると除外混入チェック）")
    args = ap.parse_args()

    tickets = Path(args.tickets)
    selected = Path(args.selected)
    exclude_json = Path(args.exclude_json) if args.exclude_json else None

    if not tickets.exists():
        print(f"[NG] tickets not found: {tickets}")
        return 2
    if not selected.exists():
        print(f"[NG] selected not found: {selected}")
        return 2

    df_t = pd.read_csv(tickets)
    df_s = pd.read_csv(selected)

    for col in ("date", "jcd", "race_no"):
        if col not in df_t.columns:
            print(f"[NG] tickets missing column: {col}")
            return 2
        if col not in df_s.columns:
            print(f"[NG] selected missing column: {col}")
            return 2

    df_t["jcd_int"] = df_t["jcd"].map(norm_jcd)
    df_s["jcd_int"] = df_s["jcd"].map(norm_jcd)

    dates_t = sorted(df_t["date"].astype(str).unique().tolist())
    dates_s = sorted(df_s["date"].astype(str).unique().tolist())

    ok = True
    if dates_t != dates_s:
        ok = False
        print(f"[NG] date mismatch: tickets={dates_t} selected={dates_s}")

    t_keys = keys(df_t)
    s_keys = keys(df_s)

    missing = sorted(s_keys - t_keys)
    if missing:
        ok = False
        print(f"[NG] selected races missing in tickets: {len(missing)} (show first 10)")
        for k in missing[:10]:
            print("  -", k)

    excl = load_excluded_jcd(exclude_json) if exclude_json else set()
    if excl:
        hit = sorted(set(df_t["jcd_int"].unique()).intersection(excl))
        if hit:
            ok = False
            print(f"[NG] excluded_jcd present in tickets: {hit}")
        else:
            print("[OK] excluded_jcd not present in tickets")

    # summary
    print("=== SUMMARY ===")
    print(f"tickets_rows          : {len(df_t)}")
    print(f"selected_rows         : {len(df_s)}")
    print(f"tickets_unique_races  : {len(t_keys)}")
    print(f"selected_unique_races : {len(s_keys)}")
    print(f"dates                : {dates_t}")

    if "tier" in df_t.columns:
        print("tier_counts:")
        print(df_t["tier"].value_counts().to_string())
    if "bet_type" in df_t.columns:
        print("bet_type_counts:")
        print(df_t["bet_type"].value_counts().to_string())

    print("[OK]" if ok else "[NG]")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
