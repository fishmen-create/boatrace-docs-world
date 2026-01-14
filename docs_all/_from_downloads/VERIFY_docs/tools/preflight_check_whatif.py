#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preflight_check_whatif.py

90D / what-if 成果物フォルダを走査して、preflight PASS/FAIL と理由を出力する簡易チェッカー。
- 命名規約（WORLD/WINDOW/VARIANT）の最低限チェック
- 必須ファイル（MANIFEST/ROI/command、BTならtickets）チェック
- MANIFEST とフォルダ名の整合（WORLD/WINDOW、BLの制約null）チェック

使い方（例）:
  python tools\preflight_check_whatif.py --whatif-root .\_whatif --out-csv .\runs\preflight_whatif_report.csv

"""

from __future__ import annotations
import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

RE_WINDOW = re.compile(r"\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}")
RE_WORLD = re.compile(r"__([A-Z]{2})__")
RE_VARIANT = re.compile(r"__v[0-9][A-Za-z0-9_\-]*__")

REQUIRED_FILES = ["MANIFEST.json", "roi_overall.csv", "roi_bytrack.csv", "command.txt"]

def parse_folder_tokens(name: str) -> Dict[str, str]:
    parts = name.split("__")
    out = {}
    # expected skeleton: BR VERIFY WHATIF WORLD WINDOW VARIANT STAMP ...
    if len(parts) >= 7:
        out["project"] = parts[0]
        out["domain"] = parts[1]
        out["stage"] = parts[2]
        out["world"] = parts[3]
        out["window"] = parts[4]
        out["variant"] = parts[5]
        out["stamp"] = parts[6]
    return out

def check_folder_name(tokens: Dict[str, str]) -> List[str]:
    errs = []
    world = tokens.get("world")
    window = tokens.get("window")
    variant = tokens.get("variant")
    if world not in ("BL", "BT"):
        errs.append("folder_missing_or_invalid_WORLD")
    if not window or not RE_WINDOW.fullmatch(window):
        errs.append("folder_missing_or_invalid_WINDOW")
    if not variant or not variant.startswith("v"):
        errs.append("folder_missing_or_invalid_VARIANT")
    return errs

def load_manifest(p: Path) -> Tuple[Dict, List[str]]:
    errs = []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data, errs
    except Exception as e:
        return {}, [f"manifest_read_error:{e.__class__.__name__}"]

def manifest_checks(tokens: Dict[str, str], manifest: Dict) -> List[str]:
    errs = []
    f_world = tokens.get("world")
    f_window = tokens.get("window")
    m_world = manifest.get("world")
    m_win = manifest.get("window", {})
    m_from = m_win.get("from")
    m_to = m_win.get("to")
    if m_world and f_world and m_world != f_world:
        errs.append("manifest_world_mismatch")
    if f_window and m_from and m_to:
        m_window = f"{m_from}_{m_to}"
        if m_window != f_window:
            errs.append("manifest_window_mismatch")
    # BL constraints must be null
    constraints = manifest.get("constraints", {})
    if f_world == "BL":
        if constraints.get("daily_cap") is not None:
            errs.append("bl_constraints_daily_cap_not_null")
        if constraints.get("exclude_jcd") is not None:
            errs.append("bl_constraints_exclude_jcd_not_null")
    return errs

def check_required_files(folder: Path, world: str) -> List[str]:
    errs = []
    for fn in REQUIRED_FILES:
        if not (folder / fn).exists():
            errs.append(f"missing:{fn}")
    if world == "BT" and not (folder / "tickets_long.csv").exists():
        errs.append("missing:tickets_long.csv")
    return errs

def iter_experiment_folders(root: Path) -> List[Path]:
    # Only direct children that look like our naming skeleton (starts with BR__VERIFY__WHATIF__)
    out = []
    if not root.exists():
        return out
    for p in root.iterdir():
        if p.is_dir() and p.name.startswith("BR__VERIFY__WHATIF__"):
            out.append(p)
    return sorted(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whatif-root", required=True, help="_whatif root folder")
    ap.add_argument("--out-csv", required=True, help="output csv path")
    args = ap.parse_args()

    root = Path(args.whatif_root)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for folder in iter_experiment_folders(root):
        tokens = parse_folder_tokens(folder.name)
        name_errs = check_folder_name(tokens)

        world = tokens.get("world", "")
        file_errs = check_required_files(folder, world if world in ("BL", "BT") else "")
        manifest_errs = []
        manifest_path = folder / "MANIFEST.json"
        manifest = {}
        if manifest_path.exists():
            manifest, me = load_manifest(manifest_path)
            manifest_errs.extend(me)
            if not me:
                manifest_errs.extend(manifest_checks(tokens, manifest))
        else:
            manifest_errs.append("missing:MANIFEST.json")

        errs = name_errs + file_errs + manifest_errs
        status = "PASS" if len(errs) == 0 else "FAIL"

        rows.append({
            "folder": str(folder),
            "name": folder.name,
            "world": tokens.get("world", ""),
            "window": tokens.get("window", ""),
            "variant": tokens.get("variant", ""),
            "status": status,
            "reasons": "|".join(errs)
        })

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["folder","name","world","window","variant","status","reasons"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # summary
    pass_n = sum(1 for r in rows if r["status"] == "PASS")
    fail_n = len(rows) - pass_n
    summary_path = out_csv.with_suffix("").with_name(out_csv.stem + "_summary.txt")
    summary_path.write_text(
        f"whatif_root={root}\nfolders={len(rows)}\nPASS={pass_n}\nFAIL={fail_n}\n",
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
