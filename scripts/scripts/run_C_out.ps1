param(
  [Parameter(Mandatory=$false)][string]$Date = (Get-Date -Format "yyyy-MM-dd"),
  [Parameter(Mandatory=$false)][string]$WorkDir = "C:\work\boatrace",
  [Parameter(Mandatory=$false)][string]$RunsDir = "C:\work\boatrace\runs",
  [Parameter(Mandatory=$false)][string]$Features = "",
  [Parameter(Mandatory=$false)][string]$PolicyByJcd = ""
)

$ErrorActionPreference = "Stop"

function Die($msg){
  Write-Host "[FATAL] $msg" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path $WorkDir)) { Die "WorkDir not found: $WorkDir" }
if (-not (Test-Path $RunsDir)) { New-Item -ItemType Directory -Force -Path $RunsDir | Out-Null }

# Decide features file
if ($Features -and (Test-Path $Features)) {
  $feat = $Features
} else {
  $cand1 = Join-Path $RunsDir ("official_features_all_{0}_dedup.csv" -f $Date)
  $cand2 = Join-Path $RunsDir ("official_features_all_{0}.csv" -f $Date)
  $cand3 = Join-Path $WorkDir ("official_features_all_{0}_dedup.csv" -f $Date)
  $cand4 = Join-Path $WorkDir ("official_features_all_{0}.csv" -f $Date)
  if (Test-Path $cand1) { $feat = $cand1 }
  elseif (Test-Path $cand2) { $feat = $cand2 }
  elseif (Test-Path $cand3) { $feat = $cand3 }
  elseif (Test-Path $cand4) { $feat = $cand4 }
  else { Die "features csv not found. Provide -Features or put official_features_all_${Date}(_dedup).csv under $RunsDir" }
}
Write-Host ("[info] FEATURES=" + $feat) -ForegroundColor Cyan

# Decide predictor script (prefer STSAFE if exists)
$s_stsafe = Join-Path $WorkDir "boatrace_backtest_v12_prune_configurable_s087_alltracks_STSAFE.py"
$s_axisfix = Join-Path $WorkDir "boatrace_backtest_v12_prune_configurable_s087_alltracks_AXISFIX.py"
$s_base   = Join-Path $WorkDir "boatrace_backtest_v12_prune_configurable_s087_alltracks.py"

$pred = ""
if (Test-Path $s_stsafe) { $pred = $s_stsafe }
elseif (Test-Path $s_axisfix) { $pred = $s_axisfix }
elseif (Test-Path $s_base) { $pred = $s_base }
else { Die "prediction scripts not found under $WorkDir" }

Write-Host ("[info] PRED_SCRIPT=" + $pred) -ForegroundColor Cyan

# Stamp / output prefix
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outPrefix = Join-Path $RunsDir ("C_OUT_{0}_{1}" -f $Date, $stamp)

# Run predictor (C output = provisional; OK even if some optional columns missing)
Write-Host "[1] run predictor (C provisional: S/A/axis/conf)" -ForegroundColor Cyan
if ($PolicyByJcd) {
  python $pred --features-csv "$feat" --date-from $Date --date-to $Date --output-prefix "$outPrefix" --policy-by-jcd "$PolicyByJcd"
} else {
  python $pred --features-csv "$feat" --date-from $Date --date-to $Date --output-prefix "$outPrefix"
}
if ($LASTEXITCODE -ne 0) { Die "predictor failed. outPrefix=$outPrefix" }

$report = "${outPrefix}_report.csv"
if (-not (Test-Path $report)) { Die "report not created: $report" }

# Emit compact C output (no money)
Write-Host "[2] emit C output (compact list; no money)" -ForegroundColor Cyan
$c_emit = Join-Path $WorkDir "scripts\c_out_emit_summary.py"
if (-not (Test-Path $c_emit)) { Die "c_out_emit_summary.py not found: $c_emit" }

$c_out = "${outPrefix}_C_race_summary.csv"
$c_txt = "${outPrefix}_C_race_summary.txt"
python $c_emit --report "$report" --out "$c_out" --txt "$c_txt"
if ($LASTEXITCODE -ne 0) { Die "c_out_emit failed" }

Write-Host ("[OK] C_OUTPUT_CSV=" + $c_out) -ForegroundColor Green
Write-Host ("[OK] C_OUTPUT_TXT=" + $c_txt) -ForegroundColor Green
