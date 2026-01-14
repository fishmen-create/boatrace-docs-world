#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""boatrace_backtest_v12.py

目的
- v1.2（S/A判定・2軸OK・買い目テンプレ・見送り条件）でバックテスト用の report / tickets を生成
- ただし「③候補の生成」だけを policy として差し替え可能にし、鳴門（jcd=14）のみ候補fix(motor+nat)を適用
  → スクリプト2本化を回避しつつ、場別の挙動差をconfigで管理

入力
- 公式features（Bファイル抽出＋K突合）CSV:
    collect_boatrace_official_features.py の出力
    例: official_features_all_20251201_31.csv
- 払戻CSV（任意。指定すると ret を計算）:
    collect_boatrace_payouts.py の出力を想定

出力
- <prefix>_report.csv  : レース単位（axis/cands/conf/tier/res/hit/retなど）
- <prefix>_tickets_long.csv : 買い目明細（3T/3Fの各行のbet含む）
- <prefix>_summary.txt : 集計

使い方（例）
  python boatrace_backtest_v12.py \
    --features-csv C:\work\boatrace\official_features_all_20251201_31.csv \
    --payouts-csv  C:\work\boatrace\payouts_naruto_20251201_31.csv \
    --date-from 2025-12-09 --date-to 2025-12-12 \
    --track 鳴門 \
    --output-prefix C:\work\boatrace\backtest_naruto_20251209_12_v12

注
- v1.2の「S/A閾値」「投資配分」は固定（S>=0.87, A>=0.60; 3T=8000, 3F=2000）
- confは0..1に収めるため、各レース内スコアの優位性から sigmoid で算出（再現性重視の単純版）
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


# ----------------------------
# 固定：v1.2 閾値 / 投資テンプレ
# ----------------------------
CONF_S = 0.87
CONF_A = 0.60
INV_PER_RACE = 10_000
INV_3T = 8_000
INV_3F = 2_000


# ----------------------------
# 追加：Aランクの暫定“切り捨て”ルール（ユーザー合意）
# - tier_raw == "A" のときのみ適用（Sは常に採用）
# - provisional: wave_cm が 2 or 3 / race_no が 5..8 のどちらかに該当 → A-（見送り）
# 目的：Aの中で期待値/的中率が低い傾向のレースを間引き、運用効率を上げる
# ※このルール自体の有効性は定期的に診断CSVで再確認する（後述）
# ----------------------------
A_PRUNE_WAVE_CM_SET = {2, 3}
A_PRUNE_RACE_NO_SET = {5, 6, 7, 8}

def decide_a_prune_provisional(tier_raw: str, wave_cm: Optional[float], race_no: int) -> Tuple[bool, str]:
    """暫定A間引き。戻り値: (pruned, reason)"""
    if tier_raw != "A":
        return False, ""
    reasons: List[str] = []
    if wave_cm is not None and not math.isnan(wave_cm):
        try:
            w = int(round(float(wave_cm)))
            if w in A_PRUNE_WAVE_CM_SET:
                reasons.append("wave_2_3cm")
        except Exception:
            pass
    if int(race_no) in A_PRUNE_RACE_NO_SET:
        reasons.append("race_5_8")
    if reasons:
        return True, "+".join(reasons)
    return False, ""



def decide_a_prune(
    mode: str,
    tier_raw: str,
    wave_cm: Optional[float],
    race_no: int,
    jcd: int,
) -> Tuple[bool, str]:
    """Aランク内の暫定“切り捨て”判定。

    mode:
      - off: 無効
      - provisional: 【全場】波高2〜3cm OR 5〜8R → A-
      - miyajima_wave23: 【宮島(jcd=17)のみ】波高2〜3cm → A-
    """
    if mode == "off":
        return False, ""
    if mode == "provisional":
        return decide_a_prune_provisional(tier_raw, wave_cm, race_no)
    if mode == "miyajima_wave23":
        if tier_raw != "A":
            return False, ""
        if int(jcd) != 17:
            return False, ""
        if wave_cm is None or (isinstance(wave_cm, float) and math.isnan(wave_cm)):
            return False, ""
        try:
            w = int(round(float(wave_cm)))
        except Exception:
            return False, ""
        if w in A_PRUNE_WAVE_CM_SET:
            # "wave_2_3cm" を含め、既存の診断分解ロジックと互換にする
            return True, "miya_wave_2_3cm"
        return False, ""
    raise ValueError(f"Unknown a_prune mode: {mode}")

# ----------------------------
# 場コード（JCD）マップ（代表的なボートレース場）
# ※全角スペース等が混ざることがあるため、正規化して使う
# ----------------------------
TRACK_NAME_TO_JCD: Dict[str, int] = {
    "桐生": 1,
    "戸田": 2,
    "江戸川": 3,
    "平和島": 4,
    "多摩川": 5,
    "浜名湖": 6,
    "蒲郡": 7,
    "常滑": 8,
    "津": 9,
    "三国": 10,
    "びわこ": 11,
    "住之江": 12,
    "尼崎": 13,
    "鳴門": 14,
    "丸亀": 15,
    "児島": 16,
    "宮島": 17,
    "徳山": 18,
    "下関": 19,
    "若松": 20,
    "芦屋": 21,
    "福岡": 22,
    "唐津": 23,
    "大村": 24,
}


def norm_track_name(s: str) -> str:
    # 全角/半角スペース除去
    return re.sub(r"[ 　]", "", str(s))


def safe_float(x, default: float = float("nan")) -> float:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def sigmoid(x: float) -> float:
    # 数値安定
    if x >= 0:
        z = math.exp(-x)
        return 1 / (1 + z)
    else:
        z = math.exp(x)
        return z / (1 + z)


def zscore_series(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    mu = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or pd.isna(sd):
        return (s - mu) * 0.0
    return (s - mu) / sd


@dataclass
class CandidatePolicy:
    name: str

    def score(self, df_boats: pd.DataFrame) -> pd.Series:
        """df_boats: レース内6艇（axisも含む）。戻り値はlane indexに対応するスコア。"""
        raise NotImplementedError


class CandidatePolicyV12(CandidatePolicy):
    """v1.2（デフォルト）: loc寄りで③候補を選ぶ"""

    def __init__(self):
        super().__init__(name="v12")

    def score(self, df_boats: pd.DataFrame) -> pd.Series:
        # ③候補用：loc重視 + nat + 機力を少し
        loc_2 = pd.to_numeric(df_boats["loc_2ren"], errors="coerce")
        nat_2 = pd.to_numeric(df_boats["nat_2ren"], errors="coerce")
        m_2 = pd.to_numeric(df_boats["motor_2ren"], errors="coerce")
        b_2 = pd.to_numeric(df_boats["boat_2ren"], errors="coerce")

        # NaNはレース内中央値で埋め（欠損過多はconfで落ちる想定）
        for s in (loc_2, nat_2, m_2, b_2):
            s.fillna(s.median(), inplace=True)

        return 0.55 * loc_2 + 0.25 * nat_2 + 0.10 * m_2 + 0.10 * b_2


class CandidatePolicyMotorNat(CandidatePolicy):
    """候補fix: motor+nat寄りで③候補を選ぶ（鳴門用）"""

    def __init__(self):
        super().__init__(name="motor_nat")

    def score(self, df_boats: pd.DataFrame) -> pd.Series:
        nat_2 = pd.to_numeric(df_boats["nat_2ren"], errors="coerce")
        m_2 = pd.to_numeric(df_boats["motor_2ren"], errors="coerce")

        for s in (nat_2, m_2):
            s.fillna(s.median(), inplace=True)

        return 0.40 * nat_2 + 0.60 * m_2


POLICY_REGISTRY: Dict[str, CandidatePolicy] = {
    "v12": CandidatePolicyV12(),
    "motor_nat": CandidatePolicyMotorNat(),
}


def parse_policy_by_jcd_arg(arg: Optional[str]) -> Dict[int, str]:
    """例: "14:motor_nat,7:v12" -> {14:"motor_nat",7:"v12"}"""
    if not arg:
        return {}
    out: Dict[int, str] = {}
    items = [x.strip() for x in arg.split(",") if x.strip()]
    for it in items:
        if ":" not in it:
            raise ValueError(f"--policy-by-jcd の形式が不正です: {it}")
        k, v = it.split(":", 1)
        jcd = int(k)
        v = v.strip()
        if v not in POLICY_REGISTRY:
            raise ValueError(f"未知のpolicy: {v}（使用可能: {list(POLICY_REGISTRY.keys())}）")
        out[jcd] = v
    return out


def decide_policy_for_race(jcd: int, policy_by_jcd: Dict[int, str]) -> CandidatePolicy:
    name = policy_by_jcd.get(jcd, "v12")
    return POLICY_REGISTRY[name]


def compute_axis_scores(df_boats: pd.DataFrame) -> pd.Series:
    """軸スコア（axis1/axis2決定用）: K + official features を素直に合成（レース内z）"""

    # 高いほど良い（st/displayは低いほど良い）
    nat2_z = zscore_series(df_boats["nat_2ren"]).fillna(0.0)
    loc2_z = zscore_series(df_boats["loc_2ren"]).fillna(0.0)
    mot2_z = zscore_series(df_boats["motor_2ren"]).fillna(0.0)
    boat2_z = zscore_series(df_boats["boat_2ren"]).fillna(0.0)
    # NOTE: Some feature exports (e.g., early-day / pre-exhibition B-only) may not contain ST / display-time columns.
    # In that case we treat them as 0.0 (neutral) so that we can still produce provisional C outputs.
    def _numcol(names, default=0.0):
        for n in names:
            if n in df_boats.columns:
                return pd.to_numeric(df_boats[n], errors="coerce")
        return pd.Series([default] * len(df_boats), index=df_boats.index, dtype="float64")

    st_raw = _numcol(["st_s", "st", "st_time_s", "st_time"], default=0.0)
    disp_raw = _numcol(["display_time_s", "display_time", "exhibition_time_s", "tenji_time_s", "tenji_time"], default=0.0)
    st_z = zscore_series(-st_raw).fillna(0.0)
    disp_z = zscore_series(-disp_raw).fillna(0.0)

    # コースは1が有利寄りとして軽く加点（過剰学習を避けて弱め）
    lane_series = (
        pd.to_numeric(df_boats["lane"], errors="coerce")
        if "lane" in df_boats.columns
        else pd.to_numeric(pd.Series(df_boats.index, index=df_boats.index), errors="coerce")
    )
    course_raw = df_boats["course"] if "course" in df_boats.columns else lane_series
    course = pd.to_numeric(course_raw, errors="coerce").fillna(lane_series)
    course_bonus = (7 - course).clip(lower=1, upper=6)  # 1->6, 6->1
    course_z = zscore_series(course_bonus).fillna(0.0)

    score = (
        0.22 * nat2_z
        + 0.28 * loc2_z
        + 0.22 * mot2_z
        + 0.10 * boat2_z
        + 0.10 * st_z
        + 0.05 * disp_z
        + 0.03 * course_z
    )

    return score


def decide_two_axis_mode(axis1_score: float, axis2_score: float) -> bool:
    # レース内z合成なので、差が小さい = 拮抗
    gap = abs(axis1_score - axis2_score)
    return gap <= 0.15


def topn_excluding(scores: pd.Series, exclude_lanes: List[int], n: int) -> List[int]:
    """Return top-n lane numbers excluding given lanes.

    IMPORTANT:
    - scores.index can be str (e.g., '1','2'...). Normalize to int so exclusion always works.
    - This implements '軸除外＋次点埋め' by taking the next best lanes after excluding axes.
    """
    if scores is None or len(scores) == 0:
        return []

    s = scores.copy()

    # Normalize index -> int lanes
    idx = pd.to_numeric(s.index, errors="coerce")
    s.index = idx
    s = s[~s.index.isna()].copy()
    s.index = s.index.astype(int)

    s = s.sort_values(ascending=False)
    exclude = set(int(x) for x in exclude_lanes if x is not None)

    out: List[int] = []
    for ln in s.index.tolist():
        if int(ln) in exclude:
            continue
        out.append(int(ln))
        if len(out) >= n:
            break
    return out


def format_res_from_finish(df_boats: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """res_3t, res_3f を作る（トップ3が取れない場合はNone）"""
    if "finish" not in df_boats.columns:
        return None, None
    fin = pd.to_numeric(df_boats["finish"], errors="coerce")
    if fin.isna().sum() >= 3:
        return None, None
    df = df_boats.copy()
    # lane列が無い（laneがindex）ケースに対応
    if "lane" not in df.columns:
        df["lane"] = df.index
    df["finish_num"] = fin
    df["lane_int"] = pd.to_numeric(df["lane"], errors="coerce")
    df = df.sort_values(["finish_num", "lane_int"], ascending=[True, True])
    top3 = df.head(3)["lane_int"].astype(int).tolist()
    if len(top3) < 3:
        return None, None
    res_3t = f"{top3[0]}-{top3[1]}-{top3[2]}"
    s3 = sorted(top3)
    res_3f = f"{s3[0]}={s3[1]}={s3[2]}"
    return res_3t, res_3f


@dataclass
class TicketLine:
    date: str
    track_name: str
    jcd: int
    race_no: int
    bet_type: str  # 3T/3F
    combo: str
    bet_yen: int


def build_tickets(
    date: str,
    track_name: str,
    jcd: int,
    race_no: int,
    axis1: int,
    axis2: int,
    cands: List[int],
    two_axis: bool,
) -> List[TicketLine]:
    # 3T lines
    tri_lines: List[str] = []
    for c in cands:
        tri_lines.append(f"{axis1}-{axis2}-{c}")
    if two_axis:
        for c in cands:
            tri_lines.append(f"{axis2}-{axis1}-{c}")

    # 3F lines（順不同）: axis1,axis2,c1/c2
    tri_f_lines: List[str] = []
    for c in cands:
        s3 = sorted([axis1, axis2, c])
        tri_f_lines.append(f"{s3[0]}={s3[1]}={s3[2]}")

    out: List[TicketLine] = []

    # 配分：均等割り
    if tri_lines:
        per = INV_3T // len(tri_lines)
        rem = INV_3T - per * len(tri_lines)
        for i, combo in enumerate(tri_lines):
            out.append(TicketLine(date, track_name, jcd, race_no, "3T", combo, per + (1 if i < rem else 0)))

    if tri_f_lines:
        per = INV_3F // len(tri_f_lines)
        rem = INV_3F - per * len(tri_f_lines)
        for i, combo in enumerate(tri_f_lines):
            out.append(TicketLine(date, track_name, jcd, race_no, "3F", combo, per + (1 if i < rem else 0)))

    return out


def calc_returns(
    tickets: List[TicketLine],
    payout_row: Optional[pd.Series],
) -> Tuple[bool, bool, int]:
    """hit_3t, hit_3f, total_ret_yen"""
    if payout_row is None or payout_row is False:
        return False, False, 0

    combo_3t = str(payout_row.get("combo_3t", ""))
    payout_3t = safe_float(payout_row.get("payout_3t"), default=float("nan"))
    combo_3f = str(payout_row.get("combo_3f", ""))
    payout_3f = safe_float(payout_row.get("payout_3f"), default=float("nan"))

    hit_3t = False
    hit_3f = False
    ret = 0

    for t in tickets:
        if t.bet_type == "3T" and combo_3t and t.combo == combo_3t and not pd.isna(payout_3t):
            hit_3t = True
            ret += int(round((t.bet_yen / 100.0) * payout_3t))
        if t.bet_type == "3F" and combo_3f and t.combo == combo_3f and not pd.isna(payout_3f):
            hit_3f = True
            ret += int(round((t.bet_yen / 100.0) * payout_3f))

    return hit_3t, hit_3f, ret


def run_self_test() -> None:
    # 最低限：policy分岐、候補2艇、軸と重複しない
    df = pd.DataFrame(
        {
            "lane": [1, 2, 3, 4, 5, 6],
            "nat_2ren": [40, 39, 38, 37, 36, 35],
            "loc_2ren": [10, 20, 30, 40, 50, 60],
            "motor_2ren": [20, 30, 40, 10, 15, 25],
            "boat_2ren": [30, 30, 30, 30, 30, 30],
            "st_s": [0.10, 0.12, 0.14, 0.16, 0.18, 0.20],
            "display_time_s": [6.80, 6.82, 6.84, 6.86, 6.88, 6.90],
            "course": [1, 2, 3, 4, 5, 6],
        }
    ).set_index("lane")

    axis_scores = compute_axis_scores(df)
    axis = axis_scores.sort_values(ascending=False).index[:2].tolist()
    axis1, axis2 = int(axis[0]), int(axis[1])

    # Naruto (jcd=14) -> motor_nat
    pol = decide_policy_for_race(14, {14: "motor_nat"})
    cand_scores = pol.score(df)
    cands = topn_excluding(cand_scores, [axis1, axis2], 2)
    assert len(cands) == 2
    assert axis1 not in cands and axis2 not in cands

    # Non-naruto (jcd=7) -> v12
    pol2 = decide_policy_for_race(7, {14: "motor_nat"})
    assert pol2.name == "v12"

    print("[ok] self-test passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["analysis","operation"], default="analysis", help="analysis=性能評価（制約なし/BL出力）, operation=運用再現（CAP/除外あり/BT出力）")
    ap.add_argument("--features-csv", required=False, help="official_features_*.csv（B抽出＋K突合）")
    ap.add_argument("--payouts-csv", default=None, help="payouts_*.csv（任意。指定するとret計算）")
    ap.add_argument("--date-from", required=False, help="YYYY-MM-DD")
    ap.add_argument("--date-to", required=False, help="YYYY-MM-DD")
    ap.add_argument("--track", default=None, help="例：鳴門（未指定なら全場）")
    ap.add_argument("--output-prefix", required=False, help="出力ファイルprefix")
    ap.add_argument(
        "--policy-by-jcd",
        default="14:motor_nat",
        help="候補生成policyをjcdで上書き（例: 14:motor_nat,7:v12）。未指定は v12。デフォルトは鳴門だけmotor_nat",
    )

    ap.add_argument(
        "--a-prune",
        choices=["off", "provisional", "miyajima_wave23"],
        default="provisional",
        help="Aランクの暫定“切り捨て”フィルタ。provisional=【全場】波高2〜3cm OR 5〜8R をA-として見送り。miyajima_wave23=【宮島(jcd=17)のみ】波高2〜3cm をA-として見送り。Sは常に採用。offで無効化。",
    )
    ap.add_argument(
        "--a-prune-history",
        default="auto",
        help="A切り捨て診断の履歴ログCSV。auto=output-prefixと同じフォルダに a_prune_history.csv を追記。空文字で無効。",
    )

    ap.add_argument(
        "--daily-cap",
        type=int,
        default=0,
        help="日次の採用上限K（S/Aのみ対象）。0で無効。例：10（=1日10Rまで）",
    )
    ap.add_argument(
        "--daily-cap-priority",
        choices=["conf", "s_then_conf"],
        default="conf",
        help="日次capの並べ替え。conf=conf降順で上位K。s_then_conf=Sを優先し、同tier内はconf降順。",
    )


    ap.add_argument(
        "--exclude-jcd",
        default="",
        help="除外する場コードjcdをカンマ区切りで指定（例: 3,6,7）。指定したjcdはS/Aでも強制SKIP（投資0/払戻0）。",
    )
    ap.add_argument(
        "--tsu-a-conf-min",
        type=float,
        default=None,
        help="津(jcd=9)の場別ルール：Aのみ採用し、conf>=この値のみを採用（SはSKIP）。未指定なら無効。",
    )

    ap.add_argument("--run-self-test", action="store_true", help="候補分岐の最低限テストを実行して終了")

    args = ap.parse_args()

    # --- v26: mode separation + date normalization ---
    def _norm_date(s: str) -> str:
        s = str(s).strip()
        if re.fullmatch(r"\d{8}", s):
            return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return s
        raise ValueError(f"Invalid date format: {s} (expected YYYYMMDD or YYYY-MM-DD)")

    if args.date_from:
        args.date_from = _norm_date(args.date_from)
    if args.date_to:
        args.date_to = _norm_date(args.date_to)

    if args.mode == "analysis":
        # analysis = 性能評価：運用制約（CAP/除外）は載せない
        if args.daily_cap is not None:
            raise SystemExit("[ERR] --mode analysis では --daily-cap を指定できません（運用制約はoperation側）")
        if args.exclude_jcd is not None:
            raise SystemExit("[ERR] --mode analysis では --exclude-jcd を指定できません（運用制約はoperation側）")

    # default paths (when omitted)
    if args.output_prefix is None:
        if not args.date_from or not args.date_to:
            raise SystemExit("[ERR] --output-prefix を省略する場合は --date-from/--date-to が必要です")
        tag = "BL" if args.mode == "analysis" else "BT"
        args.output_prefix = str(Path("runs") / f"{tag}_{args.date_from}_{args.date_to}")

    if args.features_csv is None:
        if not args.date_from or not args.date_to:
            raise SystemExit("[ERR] --features-csv を省略する場合は --date-from/--date-to が必要です")
        cand = Path("runs") / f"official_features_alltracks_{args.date_from}_{args.date_to}_dedup.csv"
        if not cand.exists():
            raise SystemExit(f"[ERR] features_csv not found: {cand}（--features-csv で明示してください）")
        args.features_csv = str(cand)

    if args.payouts_csv is None:
        if not args.date_from or not args.date_to:
            # payouts無しでも動く設計だが、ここでは明示要求（ret算出が変わるため）
            raise SystemExit("[ERR] --payouts-csv を省略する場合は --date-from/--date-to が必要です")
        cand1 = Path("runs") / f"payouts_all_{args.date_from}_{args.date_to}_MERGED_keynorm_90d.csv"
        cand2 = Path("runs") / f"payouts_all_{args.date_from}_{args.date_to}.csv"
        if cand1.exists():
            args.payouts_csv = str(cand1)
        elif cand2.exists():
            args.payouts_csv = str(cand2)
        else:
            # payouts指定なしでも tickets は作れる場合があるが、90D検証では原則必要
            raise SystemExit(f"[ERR] payouts_csv not found: {cand1} or {cand2}（--payouts-csv で明示してください）")


    if args.run_self_test:
        run_self_test()
        return

    # required args check (skip when --run-self-test)
    missing = []
    for k in ["features_csv", "date_from", "date_to", "output_prefix"]:
        if getattr(args, k) in [None, ""]:
            missing.append("--" + k.replace("_", "-"))
    if missing:
        raise SystemExit("Missing required args: " + ", ".join(missing))

    dfrom, dto = args.date_from, args.date_to
    track_filter = norm_track_name(args.track) if args.track else None
    policy_by_jcd = parse_policy_by_jcd_arg(args.policy_by_jcd)

    df = pd.read_csv(args.features_csv)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["track_norm"] = df["track_name"].map(norm_track_name)
    df["jcd"] = df["track_norm"].map(TRACK_NAME_TO_JCD)

    # filter
    df = df[(df["date"] >= dfrom) & (df["date"] <= dto)].copy()
    if track_filter:
        df = df[df["track_norm"] == track_filter].copy()

    if df.empty:
        raise SystemExit("指定範囲に一致するデータがありません（date/trackを確認）。")

    # payouts
    payout_map = None
    if args.payouts_csv:
        dfp = pd.read_csv(args.payouts_csv)
        dfp["date"] = pd.to_datetime(dfp["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        if "track_name" in dfp.columns:
            dfp["track_norm"] = dfp["track_name"].map(norm_track_name)
        else:
            dfp["track_norm"] = track_filter or ""
        # key: (date, track_norm, race_no)
        payout_map = {
            (r["date"], r["track_norm"], int(r["race_no"])): r
            for _, r in dfp.iterrows()
        }

    # group by race
    report_rows: List[Dict] = []
    ticket_rows: List[Dict] = []

    race_keys = ["date", "track_norm", "race_no"]
    for (ymd, tnorm, rno), g in df.groupby(race_keys, sort=True):
        # 1レース=6艇の想定。laneでindex化
        g2 = g.copy()
        g2["lane"] = pd.to_numeric(g2["lane"], errors="coerce")
        g2 = g2.dropna(subset=["lane"]).copy()
        g2["lane"] = g2["lane"].astype(int)
        g2 = g2.sort_values("lane")
        if g2["lane"].nunique() < 6:
            # 欠場/中止/抽出ミスなど
            continue

        track_name = str(g2["track_name"].iloc[0])
        jcd = int(g2["jcd"].iloc[0]) if not pd.isna(g2["jcd"].iloc[0]) else -1

        df_boats = g2.set_index("lane")

        # 軸
        axis_scores = compute_axis_scores(df_boats)
        axis_sorted = axis_scores.sort_values(ascending=False)
        axis1 = int(axis_sorted.index[0])
        axis2 = int(axis_sorted.index[1])
        two_axis = decide_two_axis_mode(float(axis_sorted.iloc[0]), float(axis_sorted.iloc[1]))

        # ③候補（policy分岐）
        policy = decide_policy_for_race(jcd, policy_by_jcd)
        cand_scores = policy.score(df_boats)
        cands = topn_excluding(cand_scores, [axis1, axis2], 2)
        # Final safety: never allow candidate list to include the axes.
        cands = [int(x) for x in cands if int(x) not in (axis1, axis2)]
        # Preserve order and uniqueness
        _seen = set()
        cands = [x for x in cands if (x not in _seen and not _seen.add(x))]

        cand_invalid = 0
        cand_invalid_reason = ""
        if len(cands) < 2:
            cand_invalid = 1
            cand_invalid_reason = "cand_lt2_after_excluding_axes"

        # conf
        scores = axis_scores
        top2_mean = float(scores.loc[[axis1, axis2]].mean())
        rest = scores.drop(index=[axis1, axis2])
        rest_mean = float(rest.mean())
        spread = float(scores.std(ddof=0))
        if spread == 0 or math.isnan(spread):
            spread = 1e-6
        raw = (top2_mean - rest_mean) / spread
        conf = float(sigmoid(raw))

        tier_raw = ""
        if conf >= CONF_S:
            tier_raw = "S"
        elif conf >= CONF_A:
            tier_raw = "A"
        else:
            tier_raw = "SKIP"

        # 追加：Aランクの暫定“切り捨て”（A-）を適用
        # tier(運用上の採用/見送り) は tier_raw から派生させる
        wave_cm_race = safe_float(g2["wave_cm"].iloc[0], default=float("nan")) if "wave_cm" in g2.columns else float("nan")
        a_pruned = False
        a_prune_reason = ""
        a_pruned, a_prune_reason = decide_a_prune(args.a_prune, tier_raw, wave_cm_race, int(rno), jcd)

        tier = tier_raw
        if tier_raw == "A" and a_pruned:
            tier = "SKIP"  # A- は見送り扱い（投資0）

        # 結果（backtest用）
        res_3t, res_3f = format_res_from_finish(df_boats)

        # tickets
        if cand_invalid:
            tickets = []
        else:
            tickets = build_tickets(ymd, track_name, jcd, int(rno), axis1, axis2, cands, two_axis)

        hit_3t = False
        hit_3f = False
        ret = 0
        if payout_map is not None:
            prow = payout_map.get((ymd, tnorm, int(rno)))
            if prow is not None:
                hit_3t, hit_3f, ret = calc_returns(tickets, prow)


        # 実際の運用（tier）と、もしS/Aなら賭けた場合（tier_raw）の両方を持つ
        # - ret_if_bet は「S/Aなら賭けた場合の払戻」を保存
        # - ret/hit_* は「実運用（A-は見送り）」での結果
        ret_if_bet = int(ret)
        hit_3t_if_bet = int(hit_3t)
        hit_3f_if_bet = int(hit_3f)

        active = tier in ["S", "A"]
        inv = INV_PER_RACE if active else 0
        if not active:
            # 見送り扱いは払戻も0として扱う（運用ROI用）
            ret = 0
            hit_3t = False
            hit_3f = False

        # 出力：SKIPも残す/残さないは方針次第だが、ここでは残して tierで判断できるようにする
        report_rows.append(
            {
                "date": ymd,
                "track_name": track_name,
                "jcd": jcd,
                "race_no": int(rno),
                "tier": tier,
                "active": int(active),
                "bet_yen_eff": int(inv) if active else 0,
                "daily_capped": 0,
                "daily_cap_k": int(args.daily_cap) if hasattr(args, "daily_cap") else 0,
                "daily_cap_rank": "",
                "daily_cap_priority": (args.daily_cap_priority if hasattr(args, "daily_cap_priority") else ""),
                "tier_raw": tier_raw,
                "a_pruned": int(a_pruned) if tier_raw == "A" else 0,
                "a_prune_reason": a_prune_reason if tier_raw == "A" else "",
                "wave_cm": (None if (math.isnan(wave_cm_race) if isinstance(wave_cm_race, float) else False) else float(wave_cm_race)),
                "ret_if_bet": int(ret_if_bet),
                "hit_3t_if_bet": int(hit_3t_if_bet),
                "hit_3f_if_bet": int(hit_3f_if_bet),
                "axis1": axis1,
                "axis2": axis2,
                "two_axis": int(two_axis),
                "cand_policy": policy.name,
                "cand_len": int(len(cands)) if cands is not None else 0,
                "cand_invalid": int(cand_invalid),
                "cand_invalid_reason": cand_invalid_reason,
                "cands": "-".join(map(str, cands)),
                "res": res_3t or "",
                "hit_3t": int(hit_3t),
                "hit_3f": int(hit_3f),
                "inv": inv,
                "ret": int(ret),
                "conf": round(conf, 6),
            }
        )

        for t in tickets:
            ticket_rows.append(
                {
                    "date": t.date,
                    "track_name": t.track_name,
                    "jcd": t.jcd,
                    "race_no": t.race_no,
                    "bet_type": t.bet_type,
                    "combo": t.combo,
                    "bet_yen": t.bet_yen,
                    "tier": tier,
                    "active": int(active),
                    "bet_yen_eff": int(t.bet_yen) if active else 0,
                    "daily_capped": 0,
                    "daily_cap_k": int(args.daily_cap) if hasattr(args, "daily_cap") else 0,
                    "daily_cap_rank": "",
                    "daily_cap_priority": (args.daily_cap_priority if hasattr(args, "daily_cap_priority") else ""),
                    "tier_raw": tier_raw,
                    "a_pruned": int(a_pruned) if tier_raw == "A" else 0,
                    "axis1": axis1,
                    "axis2": axis2,
                    "cands": "-".join(map(str, cands)),
                    "cand_policy": policy.name,
                }
            )

    if not report_rows:
        raise SystemExit("レースが生成されませんでした（欠場/抽出不足の可能性）。")



    # --- pre-cap gating (場別除外など：capの前に適用する) ---
    exclude_jcd = set()
    if getattr(args, "exclude_jcd", ""):
        try:
            exclude_jcd = {int(x.strip()) for x in str(args.exclude_jcd).split(",") if x.strip()}
        except Exception:
            print(f"WARNING: failed to parse --exclude-jcd={args.exclude_jcd!r}. Ignored.")
            exclude_jcd = set()

    tsu_a_conf_min = getattr(args, "tsu_a_conf_min", None)
    if tsu_a_conf_min is not None:
        try:
            tsu_a_conf_min = float(tsu_a_conf_min)
        except Exception:
            print(f"WARNING: failed to parse --tsu-a-conf-min={tsu_a_conf_min!r}. Ignored.")
            tsu_a_conf_min = None

    if exclude_jcd or tsu_a_conf_min is not None:
        for row in report_rows:
            if row.get("tier") not in ("S", "A"):
                continue

            j = int(row.get("jcd", -1))
            c = float(row.get("conf", 0.0))

            forced_skip = False
            forced_reason = ""

            if exclude_jcd and j in exclude_jcd:
                forced_skip = True
                forced_reason = "exclude_jcd"

            # 津(jcd=9)：Aのみ + conf>=min（SはSKIP）
            if not forced_skip and tsu_a_conf_min is not None and j == 9:
                if row.get("tier") != "A" or c < tsu_a_conf_min:
                    forced_skip = True
                    forced_reason = f"tsu_a_conf_min({tsu_a_conf_min})"

            if forced_skip:
                row["tier"] = "SKIP"
                row["active"] = 0
                row["inv"] = 0
                row["bet_yen_eff"] = 0
                row["ret"] = 0
                row["hit_3t"] = 0
                row["hit_3f"] = 0
                row["filter_excluded"] = 1
                row["filter_excluded_reason"] = forced_reason
            else:
                row["filter_excluded"] = 0
                row["filter_excluded_reason"] = ""

    # --- daily cap post-processing (運用負荷に合わせて日次の採用上限をかける) ---
    if getattr(args, "daily_cap", 0) and int(args.daily_cap) > 0:
        K = int(args.daily_cap)

        # date -> list of (idx, tier, conf)
        by_date = {}
        for i, row in enumerate(report_rows):
            if row.get("tier") in ("S", "A"):
                by_date.setdefault(str(row.get("date")), []).append((i, row.get("tier"), float(row.get("conf", 0.0))))

        keep_idx = set()
        for d, items in by_date.items():
            if args.daily_cap_priority == "s_then_conf":
                # S優先、その後A。tier内はconf降順
                items_sorted = sorted(items, key=lambda x: (0 if x[1] == "S" else 1, -x[2]))
            else:
                # conf降順
                items_sorted = sorted(items, key=lambda x: -x[2])

            kept = items_sorted[:K]
            for rank, (i, _tier, _conf) in enumerate(kept, start=1):
                keep_idx.add(i)
                report_rows[i]["daily_cap_rank"] = str(rank)

        # Apply: keep_idxに入っていないS/AはSKIP化（投資0, 払戻0）
        for i, row in enumerate(report_rows):
            if row.get("tier") in ("S", "A") and i not in keep_idx:
                row["daily_capped"] = 1
                row["tier"] = "SKIP"
                row["active"] = 0
                row["inv"] = 0
                row["bet_yen_eff"] = 0
                row["ret"] = 0
                row["hit_3t"] = 0
                row["hit_3f"] = 0
            # kept or originally SKIP
            elif row.get("tier") in ("S", "A"):
                row["daily_capped"] = 0
                row["active"] = 1
                row["bet_yen_eff"] = int(row.get("inv", 0))

        # Ticketsも同期：reportの最終active/tierに合わせて bet_yen_eff を0/原額にする
        active_map = {}
        tier_map = {}
        capped_map = {}
        for row in report_rows:
            key = (str(row.get("date")), int(row.get("jcd", -1)), int(row.get("race_no", -1)))
            active_map[key] = int(row.get("active", 0))
            tier_map[key] = str(row.get("tier", "SKIP"))
            capped_map[key] = int(row.get("daily_capped", 0))

        for tr in ticket_rows:
            key = (str(tr.get("date")), int(tr.get("jcd", -1)), int(tr.get("race_no", -1)))
            act = active_map.get(key, 0)
            tr["active"] = int(act)
            tr["tier"] = tier_map.get(key, tr.get("tier", "SKIP"))
            tr["daily_capped"] = int(capped_map.get(key, 0))
            tr["bet_yen_eff"] = int(tr.get("bet_yen", 0)) if act else 0

    df_report = pd.DataFrame(report_rows)

    # v1.2運用は S/Aだけ採用（SKIPは投資0）
    df_sa = df_report[df_report["tier"].isin(["S", "A"])].copy()

    total_inv = int(df_sa["inv"].sum())
    total_ret = int(df_sa["ret"].sum())
    roi = (total_ret / total_inv) if total_inv > 0 else 0.0

    # hit率
    n_sa = len(df_sa)
    hit_any = int(((df_sa["hit_3t"] == 1) | (df_sa["hit_3f"] == 1)).sum())


    # ----------------------------
    # 追加：A間引き（a-prune）の診断（定期チェック用）
    # - 今回の出力prefixごとに diagnostic CSV を生成
    # - さらに履歴ログ（a_prune_history.csv）に追記（無効化可）
    # ----------------------------
    df_a = df_report[df_report["tier_raw"] == "A"].copy() if "tier_raw" in df_report.columns else pd.DataFrame()
    diag_rows: List[Dict] = []

    def _add_diag_row(label: str, d: pd.DataFrame) -> None:
        if d is None or d.empty:
            return
        n = int(len(d))
        inv_if = INV_PER_RACE * n  # Aは1R=1万円の前提
        ret_if = int(d.get("ret_if_bet", 0).sum())
        hit_any_if = int(((d.get("hit_3t_if_bet", 0) == 1) | (d.get("hit_3f_if_bet", 0) == 1)).sum())
        roi_if = (ret_if / inv_if) if inv_if > 0 else 0.0

        inv_act = int(d.get("inv", 0).sum())
        ret_act = int(d.get("ret", 0).sum())
        hit_any_act = int(((d.get("hit_3t", 0) == 1) | (d.get("hit_3f", 0) == 1)).sum())
        roi_act = (ret_act / inv_act) if inv_act > 0 else 0.0

        diag_rows.append(
            {
                "label": label,
                "n_races": n,
                "hit_any_if_bet": hit_any_if,
                "hit_rate_if_bet": round(hit_any_if / n, 4) if n else 0.0,
                "inv_if_bet": inv_if,
                "ret_if_bet": ret_if,
                "roi_if_bet": round(roi_if, 4),
                "hit_any_actual": hit_any_act,
                "hit_rate_actual": round(hit_any_act / n, 4) if n else 0.0,
                "inv_actual": inv_act,
                "ret_actual": ret_act,
                "roi_actual": round(roi_act, 4),
                "avg_conf": round(float(pd.to_numeric(d.get("conf", pd.Series([], dtype=float)), errors="coerce").mean()), 4)
                if "conf" in d.columns
                else None,
            }
        )

    if args.a_prune != "off" and not df_a.empty:
        _add_diag_row("A_all", df_a)

        df_ap = df_a[df_a.get("a_pruned", 0) == 0]
        df_am = df_a[df_a.get("a_pruned", 0) == 1]
        _add_diag_row("A_plus", df_ap)
        _add_diag_row("A_minus", df_am)

        # 理由別（wave/race/both）
        r = df_a.get("a_prune_reason", pd.Series([""] * len(df_a), index=df_a.index)).fillna("").astype(str)
        wave = r.str.contains("wave_2_3cm", regex=False)
        mid = r.str.contains("race_5_8", regex=False)
        _add_diag_row("A_minus_wave_only", df_a[wave & ~mid])
        _add_diag_row("A_minus_mid_only", df_a[~wave & mid])
        _add_diag_row("A_minus_both", df_a[wave & mid])
        _add_diag_row("A_plus_none", df_a[~wave & ~mid])

    df_diag = pd.DataFrame(diag_rows)

    out_prefix = Path(args.output_prefix)
    out_report = str(out_prefix) + "_report.csv"
    out_tickets = str(out_prefix) + "_tickets_long.csv"
    out_summary = str(out_prefix) + "_summary.txt"


    out_diag = str(out_prefix) + "_a_prune_diagnostic.csv"

    hist_path: Optional[Path] = None
    if args.a_prune_history is not None:
        hist_arg = str(args.a_prune_history)
        if hist_arg.strip() == "":
            hist_path = None
        elif hist_arg.strip().lower() == "auto":
            hist_path = out_prefix.parent / "a_prune_history.csv"
        else:
            hist_path = Path(hist_arg)

    # report: ユーザーが求めていたヘッダ互換（必要列は維持しつつ、追加列も残す）
    # 先頭を date,race_no,tier,axis1,axis2,cands,res,hit_3t,hit_3f,inv,ret,conf に寄せる
    base_cols = ["date", "race_no", "tier", "axis1", "axis2", "cands", "res", "hit_3t", "hit_3f", "inv", "ret", "conf"]
    rest_cols = [c for c in df_report.columns if c not in base_cols]
    df_report = df_report[base_cols + rest_cols]

    df_report.to_csv(out_report, index=False, encoding="utf-8-sig")
    pd.DataFrame(ticket_rows).to_csv(out_tickets, index=False, encoding="utf-8-sig")


    # A間引き診断（任意）
    try:
        df_diag.to_csv(out_diag, index=False, encoding="utf-8-sig")
    except Exception:
        pass

    # 履歴ログ追記（任意）
    if hist_path is not None:
        try:
            hist_path.parent.mkdir(parents=True, exist_ok=True)
            row = {
                "run_ts": pd.Timestamp.now(tz="Asia/Tokyo").strftime("%Y-%m-%d %H:%M:%S%z"),
                "features_csv": Path(args.features_csv).name,
                "payouts_csv": Path(args.payouts_csv).name if args.payouts_csv else "",
                "date_from": dfrom,
                "date_to": dto,
                "track": args.track or "",
                "a_prune": args.a_prune,
                "sa_races": int(n_sa),
                "sa_hit_any": int(hit_any),
                "sa_inv": int(total_inv),
                "sa_ret": int(total_ret),
                "sa_roi": round(roi, 6),
            }
            if isinstance(df_diag, pd.DataFrame) and not df_diag.empty:
                m = df_diag[df_diag["label"] == "A_minus"]
                if not m.empty:
                    row.update({
                        "a_minus_n": int(m["n_races"].iloc[0]),
                        "a_minus_roi_if_bet": float(m["roi_if_bet"].iloc[0]),
                        "a_minus_roi_actual": float(m["roi_actual"].iloc[0]),
                    })
            if hist_path.exists():
                pd.DataFrame([row]).to_csv(hist_path, mode="a", header=False, index=False, encoding="utf-8-sig")
            else:
                pd.DataFrame([row]).to_csv(hist_path, mode="w", header=True, index=False, encoding="utf-8-sig")
        except Exception:
            pass


    # --- extra summaries (by track / by day / conf bins) ---
    def _auc_rank(y: pd.Series, s: pd.Series) -> float:
        """AUC via rank method (no external deps). Returns NaN if undefined."""
        y = pd.Series(y).astype(int)
        s = pd.Series(s).astype(float)
        mask = y.notna() & s.notna()
        y = y[mask]
        s = s[mask]
        n_pos = int((y == 1).sum())
        n_neg = int((y == 0).sum())
        if n_pos == 0 or n_neg == 0:
            return float("nan")
        # average ranks for ties
        ranks = s.rank(method="average")
        sum_ranks_pos = float(ranks[y == 1].sum())
        auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
        return float(auc)

    # columns fallback (when payouts_csv is not provided)
    hit3t_col = "hit_3t_if_bet" if "hit_3t_if_bet" in df_report.columns else "hit_3t"
    hit3f_col = "hit_3f_if_bet" if "hit_3f_if_bet" in df_report.columns else "hit_3f"
    ret_col = "ret_if_bet" if "ret_if_bet" in df_report.columns else "ret"

    df_summ_base = df_report.copy()
    df_summ_base["is_bet"] = (df_summ_base.get("inv", 0) > 0).astype(int)
    df_summ_base["hit_any"] = ((df_summ_base.get(hit3t_col, 0) == 1) | (df_summ_base.get(hit3f_col, 0) == 1)).astype(int)

    # by track (jcd + track_name)
    if "track_name" in df_summ_base.columns:
        gcols = ["jcd", "track_name"]
    else:
        gcols = ["jcd"]

    def _track_agg(df: pd.DataFrame) -> pd.Series:
        inv = float(df["inv"].sum())
        ret = float(df[ret_col].sum())
        bets = df[df["inv"] > 0]
        n_bet = int(len(bets))
        n_s = int((df["tier"] == "S").sum())
        n_a = int((df["tier"] == "A").sum())
        n_skip = int((df["tier"] == "SKIP").sum())
        n_pruned = int(df.get("a_pruned", 0).sum()) if "a_pruned" in df.columns else 0

        def _rate(series: pd.Series) -> float:
            return float(series.mean()) if len(series) else float("nan")

        hit3t = _rate(bets.get(hit3t_col, pd.Series(dtype=float)))
        hit3f = _rate(bets.get(hit3f_col, pd.Series(dtype=float)))
        hit_any = _rate(bets.get("hit_any", pd.Series(dtype=float)))

        conf = bets.get("conf", pd.Series(dtype=float))
        q = conf.quantile([0.5, 0.75, 0.9, 0.95]).to_dict() if len(conf) else {}

        auc3t = _auc_rank(bets.get(hit3t_col, pd.Series(dtype=float)), bets.get("conf", pd.Series(dtype=float)))
        auc_any = _auc_rank(bets.get("hit_any", pd.Series(dtype=float)), bets.get("conf", pd.Series(dtype=float)))

        roi = (ret / inv) if inv > 0 else float("nan")

        return pd.Series(
            {
                "n_total": int(len(df)),
                "n_bet": n_bet,
                "n_S": n_s,
                "n_A": n_a,
                "n_SKIP": n_skip,
                "n_A_pruned": n_pruned,
                "inv_sum": inv,
                "ret_sum": ret,
                "roi": roi,
                "hit3t_rate": hit3t,
                "hit3f_rate": hit3f,
                "hit_any_rate": hit_any,
                "conf_mean": float(conf.mean()) if len(conf) else float("nan"),
                "conf_p50": float(q.get(0.5, float("nan"))),
                "conf_p75": float(q.get(0.75, float("nan"))),
                "conf_p90": float(q.get(0.9, float("nan"))),
                "conf_p95": float(q.get(0.95, float("nan"))),
                "auc_conf_vs_hit3t": auc3t,
                "auc_conf_vs_hit_any": auc_any,
            }
        )

    try:
        df_bytrack = df_summ_base.groupby(gcols, dropna=False).apply(_track_agg).reset_index()
        out_bytrack = str(Path(args.output_prefix + "_summary_bytrack.csv"))
        df_bytrack.to_csv(out_bytrack, index=False, encoding="utf-8-sig")
    except Exception:
        out_bytrack = "(failed)"

    # by day (overall + by track)
    try:
        df_day = (
            df_summ_base.groupby(["date"], dropna=False)
            .apply(lambda d: pd.Series({
                "n_total": int(len(d)),
                "n_bet": int((d["inv"]>0).sum()),
                "n_S": int((d["tier"]=="S").sum()),
                "n_A": int((d["tier"]=="A").sum()),
                "n_SKIP": int((d["tier"]=="SKIP").sum()),
                "inv_sum": float(d["inv"].sum()),
                "ret_sum": float(d[ret_col].sum()),
                "roi": float(d[ret_col].sum()/d["inv"].sum()) if float(d["inv"].sum())>0 else float("nan"),
                "hit3t_rate": float(d.loc[d["inv"]>0, hit3t_col].mean()) if int((d["inv"]>0).sum()) else float("nan"),
                "hit3f_rate": float(d.loc[d["inv"]>0, hit3f_col].mean()) if int((d["inv"]>0).sum()) else float("nan"),
                "hit_any_rate": float(d.loc[d["inv"]>0, "hit_any"].mean()) if int((d["inv"]>0).sum()) else float("nan"),
                "conf_mean": float(d.loc[d["inv"]>0, "conf"].mean()) if int((d["inv"]>0).sum()) else float("nan"),
            }))
            .reset_index()
            .sort_values("date")
        )
        out_byday = str(Path(args.output_prefix + "_summary_byday.csv"))
        df_day.to_csv(out_byday, index=False, encoding="utf-8-sig")
    except Exception:
        out_byday = "(failed)"

    # conf bins (overall)
    try:
        bins = [0.0, 0.60, 0.70, 0.80, 0.85, 0.87, 0.90, 1.01]
        labels = ["<0.60", "0.60-0.70", "0.70-0.80", "0.80-0.85", "0.85-0.87", "0.87-0.90", ">=0.90"]
        bets = df_summ_base[df_summ_base["inv"]>0].copy()
        bets["conf_bin"] = pd.cut(bets["conf"], bins=bins, labels=labels, right=False, include_lowest=True)
        df_bins = (
            bets.groupby("conf_bin", dropna=False)
            .apply(lambda d: pd.Series({
                "n_bet": int(len(d)),
                "hit3t_rate": float(d[hit3t_col].mean()) if len(d) else float("nan"),
                "hit3f_rate": float(d[hit3f_col].mean()) if len(d) else float("nan"),
                "hit_any_rate": float(d["hit_any"].mean()) if len(d) else float("nan"),
                "roi": float(d[ret_col].sum()/d["inv"].sum()) if float(d["inv"].sum())>0 else float("nan"),
                "conf_mean": float(d["conf"].mean()) if len(d) else float("nan"),
            }))
            .reset_index()
        )
        out_bins = str(Path(args.output_prefix + "_summary_confbins.csv"))
        df_bins.to_csv(out_bins, index=False, encoding="utf-8-sig")
    except Exception:
        out_bins = "(failed)"

    summary_lines = []
    summary_lines.append("=== v1.2 backtest summary ===")
    summary_lines.append(f"features_csv: {args.features_csv}")
    summary_lines.append(f"payouts_csv:  {args.payouts_csv or '(none)'}")
    summary_lines.append(f"date: {dfrom}..{dto}")
    summary_lines.append(f"track: {args.track or '(all)'}")
    summary_lines.append(f"policy_by_jcd: {args.policy_by_jcd}")

    summary_lines.append(f"a_prune: {args.a_prune}")
    summary_lines.append(f"a_prune_history: {hist_path if hist_path is not None else '(disabled)'}")
    summary_lines.append(f"a_prune_diagnostic_csv: {out_diag}")
    summary_lines.append(f"summary_bytrack_csv: {out_bytrack}")
    summary_lines.append(f"summary_byday_csv:   {out_byday}")
    summary_lines.append(f"summary_confbins_csv:{out_bins}")
    summary_lines.append("")
    summary_lines.append(f"S/A races: {n_sa}")
    summary_lines.append(f"Hit(any):  {hit_any}/{n_sa}  ({(hit_any/n_sa if n_sa else 0):.3f})")
    summary_lines.append(f"Invest:    {total_inv}")
    summary_lines.append(f"Return:    {total_ret}")
    summary_lines.append(f"ROI:       {roi:.3f}")

    Path(out_summary).write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"[ok] wrote report:  {out_report}")
    print(f"[ok] wrote tickets: {out_tickets}")
    print(f"[ok] wrote summary: {out_summary}")
    print(f"[ok] wrote diagnostic: {out_diag}")
    print(f"[ok] wrote bytrack: {out_bytrack}")
    print(f"[ok] wrote byday:   {out_byday}")
    print(f"[ok] wrote confbins:{out_bins}")


if __name__ == "__main__":
    main()
