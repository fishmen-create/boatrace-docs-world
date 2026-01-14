import argparse, re
import pandas as pd

def pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def is_3t(s: str) -> bool:
    u = str(s).upper()
    return ("3T" in u) or ("3連単" in s) or ("三連単" in s)

def is_3f(s: str) -> bool:
    u = str(s).upper()
    return ("3F" in u) or ("3連複" in s) or ("三連複" in s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--diag", required=True)
    ap.add_argument("--wave_th", type=float, default=7.0)
    ap.add_argument("--alloc3t", type=float, default=0.65)  # rough時 3T比率
    args = ap.parse_args()

    t = pd.read_csv(args.tickets, low_memory=False, dtype=str)
    bet_col = pick(t, ["bet_yen_eff","bet_yen","bet"])
    bt_col  = pick(t, ["bet_type","type"])
    d_col   = pick(t, ["date","ymd"])
    j_col   = pick(t, ["jcd","track","track_code"])
    r_col   = pick(t, ["race_no","race","rno"])
    if None in (bet_col, bt_col, d_col, j_col, r_col):
        raise SystemExit(f"tickets key missing: bet={bet_col} bet_type={bt_col} date={d_col} jcd={j_col} race={r_col}")

    t[bet_col] = pd.to_numeric(t[bet_col], errors="coerce").fillna(0).astype(int)

    rep = pd.read_csv(args.report, low_memory=False, dtype=str)
    rd = pick(rep, ["date","ymd"])
    rj = pick(rep, ["jcd","track","track_code"])
    rr = pick(rep, ["race_no","race","rno"])
    wave = pick(rep, ["wave_cm","wave","wave_h","波高"])
    tier = pick(rep, ["tier","rank","rank_tier"])
    if None in (rd,rj,rr,wave):
        raise SystemExit(f"report key missing: date={rd} jcd={rj} race={rr} wave={wave}")

    rep["_wave"] = pd.to_numeric(rep[wave], errors="coerce")
    rep["_rough"] = (rep["_wave"].fillna(-1) >= args.wave_th).astype(int)

    # Sのみ（tierが無い場合は全対象扱いにするが、diagに残す）
    if tier:
        rep["_isS"] = (rep[tier].astype(str).str.upper() == "S").astype(int)
        tier_missing = 0
    else:
        rep["_isS"] = 1
        tier_missing = 1

    key = rep[[rd,rj,rr,"_rough","_isS"]].copy()
    key.columns = [d_col,j_col,r_col,"rough_flag","isS"]

    out = t.merge(key, on=[d_col,j_col,r_col], how="left")
    out["rough_flag"] = out["rough_flag"].fillna(0).astype(int)
    out["isS"] = out["isS"].fillna(0).astype(int)

    alloc3t = float(args.alloc3t)
    alloc3f = 1.0 - alloc3t

    diag = []
    # 対象レースのみ走査（速度とdiag削減）
    targets = out[(out["rough_flag"]==1) & (out["isS"]==1)]
    if targets.empty:
        out.to_csv(args.out, index=False, encoding="utf-8")
        pd.DataFrame([{"status":"NO_TARGET","tier_missing":tier_missing}]).to_csv(args.diag, index=False, encoding="utf-8")
        return

    grp_cols = [d_col,j_col,r_col]
    for (d,j,r), g in out.groupby(grp_cols, sort=False):
        rough = int(g["rough_flag"].iloc[0])
        isS = int(g["isS"].iloc[0])
        if not (rough==1 and isS==1):
            continue

        bt = g[bt_col].astype(str)
        m3t = bt.map(is_3t)
        m3f = bt.map(is_3f)

        cur3t = g.loc[m3t, bet_col].sum()
        cur3f = g.loc[m3f, bet_col].sum()
        total = int(cur3t + cur3f)

        if total <= 0 or cur3t <= 0 or cur3f <= 0:
            diag.append({"date":d,"jcd":j,"race":r,"status":"SKIP_NO_SPLIT","cur3t":int(cur3t),"cur3f":int(cur3f),"total":total})
            continue

        tgt3t = int(round(total * alloc3t))
        tgt3f = total - tgt3t
        f3t = tgt3t / cur3t
        f3f = tgt3f / cur3f

        idx = g.index
        # 100円単位へ丸め（-2）
        out.loc[idx[m3t.values], bet_col] = (out.loc[idx[m3t.values], bet_col] * f3t).round(-2).astype(int)
        out.loc[idx[m3f.values], bet_col] = (out.loc[idx[m3f.values], bet_col] * f3f).round(-2).astype(int)

        new3t = int(out.loc[idx[m3t.values], bet_col].sum())
        new3f = int(out.loc[idx[m3f.values], bet_col].sum())
        new_total = new3t + new3f
        delta = total - new_total
        if delta != 0:
            # 3T側の最大ベット行に吸収（無ければ3F側）
            if m3t.any():
                k = out.loc[idx[m3t.values], bet_col].idxmax()
            else:
                k = out.loc[idx[m3f.values], bet_col].idxmax()
            out.loc[k, bet_col] = int(out.loc[k, bet_col]) + int(delta)

        diag.append({
            "date":d,"jcd":j,"race":r,"status":"SWITCH",
            "wave_th":args.wave_th,"alloc_after":f"{alloc3t:.2f}/{alloc3f:.2f}",
            "cur3t":int(cur3t),"cur3f":int(cur3f),"total":total,
            "new3t":new3t,"new3f":new3f
        })

    out.to_csv(args.out, index=False, encoding="utf-8")
    pd.DataFrame(diag).to_csv(args.diag, index=False, encoding="utf-8")

if __name__ == "__main__":
    main()
