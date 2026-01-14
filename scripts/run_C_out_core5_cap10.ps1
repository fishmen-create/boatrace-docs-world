# PATCH_ID: HITLOSS6040_v5
param(
  [Parameter(Mandatory=$true)][string]$Date,
  [string]$WorkDir,
  [string]$RunDir,
  [int]$Cap = 10,
  [ValidateSet("OFF","A_ST3_6040")][string]$HitLossMode = "A_ST3_6040",
  [string]$FeaturesCsv,
  [switch]$NoHitLoss
)

$ErrorActionPreference = "Stop"

function Resolve-Abs([string]$p){
  if([string]::IsNullOrWhiteSpace($p)){ return $null }
  return (Resolve-Path -LiteralPath $p).Path
}

# WorkDir default = repo root (scripts\..)
if([string]::IsNullOrWhiteSpace($WorkDir)){
  $WorkDir = Join-Path $PSScriptRoot ".."
}
$WorkDir = Resolve-Abs $WorkDir
if(-not $WorkDir){ throw "WorkDir is empty. Provide -WorkDir C:\work\boatrace" }

# RunDir default = <WorkDir>\runs
if([string]::IsNullOrWhiteSpace($RunDir)){
  $RunDir = Join-Path $WorkDir "runs"
}
$RunDir = Resolve-Abs $RunDir
if(-not $RunDir){ throw "RunDir is empty. Provide -RunDir C:\work\boatrace\runs" }

Write-Host ("[run_C_out_core5_cap10] PATCH_ID=HITLOSS6040_v5 Date={0} Cap={1} HitLossMode={2} WorkDir={3} RunDir={4}" -f $Date,$Cap,$HitLossMode,$WorkDir,$RunDir)
if(-not (Test-Path -LiteralPath $RunDir)){ throw "RunDir does not exist: $RunDir" }


# Validate Date
if([string]::IsNullOrWhiteSpace($Date)){
  throw "Date is empty. Usage: run_C_out_core5_cap10.ps1 -Date YYYY-MM-DD"
}

$run = Join-Path $RunDir ("C_OUT_FIXED_{0}" -f $Date)
if(-not (Test-Path -LiteralPath $run)){
  throw "Run dir not found: $run"
}

# Find input races/tickets (prefer CAP10 artifacts produced by Cフェーズ)
$races = Get-ChildItem -LiteralPath $run -File -Filter "*CAP10*races*.csv" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $races){
  $races = Get-ChildItem -LiteralPath $run -File -Filter "*races*.csv" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if(-not $races){
  Write-Host "[debug] listing files under: $run"
  Get-ChildItem -LiteralPath $run -File | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName,LastWriteTime,Length | Format-Table -AutoSize | Out-String | Write-Host
  throw "races csv not found under $run"
}

$tickets = Get-ChildItem -LiteralPath $run -File -Filter "*CAP10*tickets_long*.csv" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $tickets){
  $tickets = Get-ChildItem -LiteralPath $run -File -Filter "*tickets_long*.csv" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if(-not $tickets){ throw "tickets_long csv not found under $run" }

$py = Join-Path $WorkDir "tools\make_core5_cap10_tickets.py"
if(-not (Test-Path -LiteralPath $py)){
  throw "make_core5_cap10_tickets.py not found: $py"
}

if($NoHitLoss){ $HitLossMode = "OFF" }

if($HitLossMode -ne "OFF"){
  if([string]::IsNullOrWhiteSpace($FeaturesCsv)){
    # Auto-pick the latest dedup features under runs
    $cand = Get-ChildItem -LiteralPath $RunDir -File -Filter "official_features_all*dedup*.csv" -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if($cand){ $FeaturesCsv = $cand.FullName }
  }
  if([string]::IsNullOrWhiteSpace($FeaturesCsv)){
    throw "FeaturesCsv required for HitLossMode=$HitLossMode. Provide -FeaturesCsv <path>"
  }
  if(-not (Test-Path -LiteralPath $FeaturesCsv)){
    throw "FeaturesCsv not found: $FeaturesCsv"
  }
}

$outPrefix = Join-Path $run "CAP10_core5"

$args = @(
  $py,
  "--race-summary-csv", $races.FullName,
  "--tickets-long-csv", $tickets.FullName,
  "--cap", "$Cap",
  "--out-prefix", $outPrefix,
  "--hitloss-mode", $HitLossMode
)

if($HitLossMode -ne "OFF"){
  $args += @("--features-csv", $FeaturesCsv)
}

Write-Host ("[RUN] python " + ($args -join " "))
& python @args
if($LASTEXITCODE -ne 0){ throw "python failed: $LASTEXITCODE" }

Write-Host "OK wrote:"
Write-Host ("  {0}_races.csv" -f $outPrefix)
Write-Host ("  {0}_tickets_long.csv" -f $outPrefix)
Write-Host ("  {0}_meta.json" -f $outPrefix)
