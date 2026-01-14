import argparse, csv, json, sys

def norm(x: str):
    s = str(x).strip()
    if s == "":
        return None
    try:
        return f"{int(s):02d}"
    except Exception:
        return s

def load_excluded(cfg):
    keys = ["excluded_jcd","excluded_jcds","excluded_tracks","excluded_tracks_jcd","excluded_jyo","excluded_jyo_cd"]
    for k in keys:
        v = cfg.get(k)
        if isinstance(v, list):
            return set(filter(None, (norm(i) for i in v)))
    for _, v in cfg.items():
        if isinstance(v, dict):
            for kk in ["excluded_jcd","excluded_jcds"]:
                vv = v.get(kk)
                if isinstance(vv, list):
                    return set(filter(None, (norm(i) for i in vv)))
    return set()

def pick(cols, cands):
    for c in cands:
        if c in cols:
            return c
    return None

def to_float(v):
    if v is None:
        return 0.0
    t = str(v).strip().replace(",", "")
    if t == "":
        return 0.0
    try:
        return float(t)
    except Exception:
        return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True)
    ap.add_argument("--exclude-config", required=True)
    ap.add_argument("--label", default="check")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    with open(args.exclude_config, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)
    excluded = load_excluded(cfg)

    only = [norm(x) for x in args.only.split(",") if norm(x)] if args.only else []
    # if only not provided, just use excluded
    target = set(only) if only else set(excluded)

    with open(args.tickets, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames or []
        j = pick(cols, ["jcd","raw_jcd","jyo_cd","jyo","track","track_norm"])
        b = pick(cols, ["bet_yen_eff","bet_yen","bet","stake","amount","yen"])
        fl = pick(cols, ["active","is_active","is_bet","bet_flag"])
        if not j:
            print(f"[P0] {args.label} ERROR: no jcd col", file=sys.stderr)
            return 2
        if not b and not fl:
            print(f"[P0] {args.label} ERROR: no bet/flag col", file=sys.stderr)
            return 2

        ex_rows = ex_act = 0
        ex_sum = 0.0
        seen = set()
        active_seen = set()

        for row in r:
            jj = norm(row.get(j))
            if jj in target:
                ex_rows += 1
                seen.add(jj)
                bet = to_float(row.get(b)) if b else 0.0
                flag = str(row.get(fl, "")).strip().lower() if fl else ""
                active = (bet > 0.0) or (flag in ("1","true","t","y","yes","on"))
                if active:
                    ex_act += 1
                    ex_sum += bet
                    active_seen.add(jj)

    status = "PASS" if ex_act == 0 and abs(ex_sum) < 1e-9 else "FAIL"
    print(f"[P0] {args.label} tickets={args.tickets}")
    print(f"[P0] {args.label} target={sorted(target)}")
    print(f"[P0] {args.label} ex_rows={ex_rows} ex_active_rows={ex_act} ex_bet_sum={ex_sum:.0f} status={status}")
    if active_seen:
        print(f"[P0] {args.label} active_excluded_jcd={sorted(active_seen)}")
    return 0 if status == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
