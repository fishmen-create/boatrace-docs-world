param(
  [string]$DateFrom = "2025-10-08",
  [string]$DateTo   = "2026-01-05",
  [string]$CandidateJson = "C:\work\boatrace\config\candidate_cap10_excl10.json",
  [string]$BaselineJson  = "C:\work\boatrace\config\baseline.json",
  [string]$PayoutsFixed  = "",
  [string]$OutDir = "C:\work\boatrace\runs"
)

$ErrorActionPreference = "Stop"
Set-Location "C:\work\boatrace"

# ---- worldline guard (avoid running a different copy by mistake) ----
$here = $PSCommandPath
$expected = "C:\work\boatrace\run_true90_compare.ps1"
if ($here -and ($here -ne $expected)) {
  Write-Host ("[WARN] invoked from: " + $here) -ForegroundColor Yellow
  Write-Host ("[WARN] expected     : " + $expected) -ForegroundColor Yellow
}

# ---- auto-detect ROI calc script ----
$roi = Get-ChildItem "C:\work\boatrace" -Filter "calc_roi_from_tickets_payouts_simple*.py" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Desc | Select-Object -First 1
if (-not $roi) { throw "ROI calc script not found: calc_roi_from_tickets_payouts_simple*.py under C:\work\boatrace" }
$roiScript = $roi.FullName
Write-Host ("[info] ROI_SCRIPT=" + $roiScript) -ForegroundColor Cyan

# ---- auto-detect CAP10 builder (prefer exclude-config capable script) ----
$cap = Get-ChildItem "C:\work\boatrace" -Filter "cap10_select_conf_top10_v3.py" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Desc | Select-Object -First 1
$capBuilder = $null
if ($cap) { $capBuilder = $cap.FullName }
if ($capBuilder) { Write-Host ("[info] CAP_BUILDER=" + $capBuilder) -ForegroundColor Cyan } else { Write-Host "[info] CAP_BUILDER=(fallback to json.cap_builder)" -ForegroundColor Cyan }


# ---- P0 guard: exclusions must be effective on final tickets (active/bet) ----
function Assert-ExclusionsEffective([string]$TicketsCsv, [string]$ExclusionsJson, [string]$Label, [string]$OnlyJcdCsv="") {
  Assert-File $TicketsCsv
  Assert-File $ExclusionsJson

  # Avoid PowerShell quoting issues by writing python checker to a temp .py and executing it
  $tmpDir = Join-Path $OutDir "_tmp"
  New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
  $pyPath = Join-Path $tmpDir "p0_check_exclusions.py"

  $py = @'
import argparse, csv, json, sys

def norm(x):
    s = str(x).strip()
    if s == "":
        return None
    try:
        return f"{int(s):02d}"
    except:
        return s

def load_excl(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)
    keys = ["excluded_jcd","excluded_jcds","excluded_tracks","excluded_tracks_jcd","excluded_jyo","excluded_jyo_cd"]
    for k in keys:
        v = cfg.get(k)
        if isinstance(v, list):
            return set(filter(None, (norm(i) for i in v)))
    for k, v in cfg.items():
        if isinstance(v, dict):
            for kk in ["excluded_jcd","excluded_jcds"]:
                vv = v.get(kk)
                if isinstance(vv, list):
                    return set(filter(None, (norm(i) for i in vv)))
    raise SystemExit("No excluded_jcd list found")

def pick(cols, cands):
    for c in cands:
        if c in cols:
            return c
    return None

def to_f(v):
    if v is None:
        return 0.0
    t = str(v).strip().replace(",", "")
    if t == "":
        return 0.0
    try:
        return float(t)
    except:
        return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True)
    ap.add_argument("--exclusions", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    ex = load_excl(args.exclusions)

    only_set = set()
    if args.only and args.only.strip():
        only_set = set(filter(None, (norm(x) for x in args.only.split(","))))
        ex = ex & only_set

    with open(args.tickets, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames or []
        j = pick(cols, ["jcd","raw_jcd","jyo_cd","jyo","track","track_norm"])
        b = pick(cols, ["bet_yen_eff","bet_yen","bet","stake","amount","yen"])
        fl = pick(cols, ["active","is_active","is_bet","bet_flag"])
        if not j:
            print(f"[P0] {args.label} ERROR: no jcd column", file=sys.stderr)
            return 3
        if not b and not fl:
            print(f"[P0] {args.label} ERROR: no bet/flag column", file=sys.stderr)
            return 3

        ex_rows = ex_act = 0
        ex_sum = 0.0
        act = set()
        seen = set()

        for row in r:
            jj = norm(row.get(j))
            if jj in ex:
                ex_rows += 1
                seen.add(jj)
                bet = to_f(row.get(b)) if b else 0.0
                flag = str(row.get(fl, "")).strip().lower() if fl else ""
                active = (bet > 0) or (flag in ("1","true","t","y","yes","on"))
                if active:
                    ex_act += 1
                    ex_sum += bet
                    act.add(jj)

    status = "PASS" if ex_act == 0 and abs(ex_sum) < 1e-9 else "FAIL"
    print(f"[P0] {args.label} ex_rows={ex_rows} ex_active_rows={ex_act} ex_bet_sum={ex_sum:.0f} status={status}")
    if only_set:
        print("[P0] only=" + ",".join(sorted(only_set)))
    print("[P0] seen=" + ",".join(sorted(seen)))

    if status == "FAIL":
        print("[P0] active_excluded_jcd=" + ",".join(sorted(act)))
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@

  Set-Content -Path $pyPath -Value $py -Encoding UTF8

  $onlyArg = ""
  if ($OnlyJcdCsv -and $OnlyJcdCsv.Trim().Length -gt 0) { $onlyArg = $OnlyJcdCsv }

  python $pyPath --tickets "$TicketsCsv" --exclusions "$ExclusionsJson" --label "$Label" --only "$onlyArg"
  if ($LASTEXITCODE -ne 0) { throw ("[P0] exclusions NOT effective: " + $Label) }
}


function Assert-File([string]$p) { if (!(Test-Path $p)) { throw ("missing file: " + $p) } }
function Detect-DateCol($row) {
  $cols = $row.PSObject.Properties.Name
  foreach ($c in @("date","race_date","日付")) { if ($cols -contains $c) { return $c } }
  return $null
}
function Filter-TicketsByDate([string]$inCsv, [string]$outCsv, [datetime]$df, [datetime]$dt) {
  $rows = Import-Csv $inCsv
  if (-not $rows -or $rows.Count -eq 0) { throw ("empty tickets: " + $inCsv) }
  $dateCol = Detect-DateCol $rows[0]
  if (-not $dateCol) {
    $cols = ($rows[0].PSObject.Properties.Name -join ",")
    throw ("date column not found in tickets. cols=" + $cols)
  }
  $filtered = @()
  foreach ($r in $rows) {
    $d = $r.$dateCol
    if (-not $d) { continue }
    try {
      $gd = Get-Date $d
      if ($gd -ge $df -and $gd -le $dt) { $filtered += $r }
    } catch { }
  }
  if ($filtered.Count -eq 0) { throw ("no rows after date filter: " + $df.ToString("yyyy-MM-dd") + ".." + $dt.ToString("yyyy-MM-dd")) }
  $filtered | Export-Csv -Path $outCsv -NoTypeInformation -Encoding UTF8
  return $filtered.Count
}

# payouts auto-pick if not specified
if (-not $PayoutsFixed -or $PayoutsFixed.Trim().Length -eq 0) {
  $p = Get-ChildItem $OutDir -Filter "payouts_all_2025-10-02_*_MERGED_keynorm.csv" | Sort-Object LastWriteTime -Desc | Select-Object -First 1
  if (-not $p) { throw "no merged payouts found in runs. expected payouts_all_2025-10-02_*_MERGED_keynorm.csv" }
  $PayoutsFixed = $p.FullName
}
Assert-File $PayoutsFixed
Assert-File $CandidateJson
Assert-File $BaselineJson

# Prefer explicit exclusions files when present (avoid worldline drift)
$candExclJson = "C:\work\boatrace\config\exclusions_EXCL10P2_candidate.json"
$baseExclJson = "C:\work\boatrace\config\exclusions.json"

$c = Get-Content $CandidateJson -Raw | ConvertFrom-Json
Assert-File $c.inputs.tickets_long
Assert-File $c.inputs.report_csv
# cap_builder is optional (we prefer auto-detected cap10_select_conf_top10_v3.py)
if (-not $capBuilder) {
  Assert-File $c.source_of_truth.cap_builder
  $capBuilder = $c.source_of_truth.cap_builder
}

# exclusions json: prefer explicit EXCL10P2 if exists, else fall back to json
if (Test-Path $candExclJson) {
  $useCandExcl = $candExclJson
} else {
  Assert-File $c.source_of_truth.exclusions_json
  $useCandExcl = $c.source_of_truth.exclusions_json
}
Write-Host ("[info] CAND_EXCLUSIONS=" + $useCandExcl) -ForegroundColor Cyan

# load candidate excluded_jcd list (for diff / debug)
$excl = (Get-Content $useCandExcl -Raw | ConvertFrom-Json).excluded_jcd
$exclStr = ($excl | ForEach-Object { $_.ToString().PadLeft(2,'0') } | Sort-Object -Unique) -join ","

# compute only_in_candidate (candidate exclusions - baseline exclusions) to catch misses like 01/17
$baselineExclJson = $baseExclJson
if (Test-Path $baselineExclJson) {
  $baseExcl = (Get-Content $baselineExclJson -Raw | ConvertFrom-Json).excluded_jcd
  $baseStr = ($baseExcl | ForEach-Object { $_.ToString().PadLeft(2,'0') } | Sort-Object -Unique) -join ","
  $onlyInCand = @()
  foreach($x in ($exclStr -split ",")) { if ($x -and (($baseStr -split ",") -notcontains $x)) { $onlyInCand += $x } }
  $onlyInCand = $onlyInCand | Sort-Object -Unique
  Write-Host ("[info] only_in_candidate=" + ($onlyInCand -join ",")) -ForegroundColor Cyan
} else {
  Write-Host ("[WARN] baseline exclusions json not found: " + $baselineExclJson) -ForegroundColor Yellow
  $onlyInCand = @()
}


$df = Get-Date $DateFrom
$dt = Get-Date $DateTo
$ts = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "== TRUE window confirm (candidate vs baseline) ==" -ForegroundColor Cyan
Write-Host ("window: " + $DateFrom + " .. " + $DateTo)
Write-Host ("payouts: " + $PayoutsFixed)

# candidate
$tmpTickets = Join-Path $OutDir ("tmp_tickets_TRUE_" + $ts + ".csv")
$capTickets = Join-Path $OutDir ("tmp_candidate_CAP10_EXCL_TRUE_" + $ts + ".csv")
$selected   = Join-Path $OutDir ("selected_races_CAP10_EXCL_TRUE_" + $ts + ".csv")
$outPrefixC = Join-Path $OutDir ("ROI_TRUE_candidate_" + $DateFrom + "_" + $DateTo + "_" + $ts)

$n = Filter-TicketsByDate $c.inputs.tickets_long $tmpTickets $df $dt
Write-Host ("[candidate] filtered rows=" + $n) -ForegroundColor Gray

# Build candidate CAP10 with exclusions
if ($capBuilder -like "*cap10_select_conf_top10_v3.py") {
  python $capBuilder --tickets "$tmpTickets" --report "$($c.inputs.report_csv)" --exclude-config "$useCandExcl" --out "$capTickets" --selected-out "$selected" --k $c.source_of_truth.cap_k
} else {
  # fallback (legacy builder): use exclude-jcd string
  python $capBuilder --tickets "$tmpTickets" --report "$($c.inputs.report_csv)" --k $c.source_of_truth.cap_k --exclude-jcd "$exclStr" --out "$capTickets" --selected-out "$selected"
}
if ($LASTEXITCODE -ne 0) { throw "cap builder failed (candidate)" }

# P0: ensure candidate exclusions are effective on final cap tickets
$onlyCsv = ""
if ($onlyInCand -and $onlyInCand.Count -gt 0) { $onlyCsv = ($onlyInCand -join ",") }
Assert-ExclusionsEffective $capTickets $useCandExcl "candidate_final" $onlyCsv


python $roiScript --tickets "$capTickets" --payouts "$PayoutsFixed" --out-prefix "$outPrefixC"
if ($LASTEXITCODE -ne 0) { throw "ROI calc failed (candidate)" }

# baseline
$b = Get-Content $BaselineJson -Raw | ConvertFrom-Json
Assert-File $b.tickets
$tmpBase    = Join-Path $OutDir ("tmp_baseline_TRUE_" + $ts + ".csv")
$outPrefixB = Join-Path $OutDir ("ROI_TRUE_baseline_" + $DateFrom + "_" + $DateTo + "_" + $ts)

$m = Filter-TicketsByDate $b.tickets $tmpBase $df $dt
Write-Host ("[baseline] filtered rows=" + $m) -ForegroundColor Gray

# P0: ensure baseline exclusions are effective on baseline final tickets
if (Test-Path $baselineExclJson) {
  Assert-ExclusionsEffective $tmpBase $baselineExclJson "baseline_final" ""
}


python $roiScript --tickets "$tmpBase" --payouts "$PayoutsFixed" --out-prefix "$outPrefixB"
if ($LASTEXITCODE -ne 0) { throw "ROI calc failed (baseline)" }

Write-Host ("candidate out_prefix: " + $outPrefixC) -ForegroundColor Cyan
Write-Host ("baseline  out_prefix: " + $outPrefixB) -ForegroundColor Cyan
Write-Host "== DONE ==" -ForegroundColor Green
