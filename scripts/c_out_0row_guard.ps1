param(
  [Parameter(Mandatory=$true)][string]$Date,
  [string]$Root = "C:\work\boatrace"
)

$ErrorActionPreference = "Stop"

$run = Join-Path (Join-Path $Root "runs") ("C_OUT_FIXED_" + $Date)
if(!(Test-Path -LiteralPath $run)){
  throw "NG: RunDir not found: $run"
}

$race = Join-Path $run "race_summary_races.csv"
$tix  = Join-Path $run "tickets_long.csv"

if(!(Test-Path -LiteralPath $race)){ throw "NG: missing: $race" }
if(!(Test-Path -LiteralPath $tix )){ throw "NG: missing: $tix" }

# row count (>=1)
$R = Import-Csv -LiteralPath $race -Encoding UTF8
$T = Import-Csv -LiteralPath $tix  -Encoding UTF8

if($R.Count -lt 1){ throw "NG: race_summary_races.csv has 0 rows: $race" }
if($T.Count -lt 1){ throw "NG: tickets_long.csv has 0 rows: $tix" }

# date match (if date col exists, require >=1)
$colsR = @($R[0].PSObject.Properties.Name)
if($colsR -contains "date"){
  $rd = ($R | Where-Object { ($_.date -as [string]).Trim() -eq $Date }).Count
  if($rd -lt 1){ throw "NG: race_summary_races.csv has no rows for Date=$Date" }
}

$colsT = @($T[0].PSObject.Properties.Name)
if($colsT -contains "date"){
  $td = ($T | Where-Object { ($_.date -as [string]).Trim() -eq $Date }).Count
  if($td -lt 1){ throw "NG: tickets_long.csv has no rows for Date=$Date" }
}

Write-Host "[OK] C_OUT inputs look valid."
Write-Host ("  RunDir : {0}" -f $run)
Write-Host ("  Races  : {0} rows ({1})" -f $R.Count, (Split-Path $race -Leaf))
Write-Host ("  Tickets: {0} rows ({1})" -f $T.Count, (Split-Path $tix -Leaf))
