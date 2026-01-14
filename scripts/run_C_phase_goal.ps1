param(
  [Parameter(Mandatory=$true)][string]$Date,
  [int]$Cap = 10
)

$ROOT = "C:\work\boatrace"
$RUNS = Join-Path $ROOT "runs"
$RUN  = Join-Path $RUNS ("C_OUT_FIXED_" + $Date)

$bat  = Join-Path $ROOT "scripts\run_C_out_core5_cap10.bat"
$ps1  = Join-Path $ROOT "scripts\run_C_out_core5_cap10.ps1"
$salv = Join-Path $ROOT "scripts\salvage_cap10_core5_from_tickets.py"

function Die($msg){
  Write-Host $msg -ForegroundColor Red
  exit 1
}

if(!(Test-Path $RUNS)){ Die "NG: runs dir not found: $RUNS" }
New-Item -ItemType Directory -Force $RUN | Out-Null

# transcript (always leaves a file)
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $RUNS ("DIAG_CPHASE_GOAL_" + $Date + "_" + $ts + ".txt")
Start-Transcript -Path $log -Append | Out-Null

Write-Host ("[C_PHASE] Date=" + $Date) -ForegroundColor Cyan
Write-Host ("[C_PHASE] RunDir=" + $RUN) -ForegroundColor Cyan
Write-Host ("[C_PHASE] Log=" + $log) -ForegroundColor Cyan

# If run dir seems to be worldline-only from a previous attempt, back it up
$hasCap = Test-Path (Join-Path $RUN "CAP10_core5_races.csv")
$hasWorld = Test-Path (Join-Path $RUN "report_worldline.csv")
if((-not $hasCap) -and $hasWorld){
  $bak = $RUN + "_WORLDLINEONLY_" + $ts
  Write-Host ("[C_PHASE] Found worldline-only dir -> rename to " + $bak) -ForegroundColor Yellow
  Rename-Item -LiteralPath $RUN -NewName (Split-Path $bak -Leaf)
  New-Item -ItemType Directory -Force $RUN | Out-Null
}

# --- Try main runner ---
$mainExit = 0
try{
  if(Test-Path $bat){
    Write-Host ("[C_PHASE] Run main via BAT: " + $bat) -ForegroundColor Cyan
    cmd /c "`"$bat`" $Date"
    $mainExit = $LASTEXITCODE
  } elseif(Test-Path $ps1){
    Write-Host ("[C_PHASE] Run main via PS1: " + $ps1) -ForegroundColor Cyan
    powershell -NoProfile -ExecutionPolicy Bypass -File $ps1 $Date
    $mainExit = $LASTEXITCODE
  } else {
    Die "NG: main runner not found: $bat / $ps1"
  }
}catch{
  Write-Host ("[C_PHASE] Main runner threw: " + $_.Exception.Message) -ForegroundColor Yellow
  $mainExit = 1
}

# --- Check core artifacts ---
$core1 = Join-Path $RUN "CAP10_core5_races.csv"
$core2 = Join-Path $RUN "CAP10_core5_tickets_long.csv"
$core3 = Join-Path $RUN "CAP10_core5_meta.json"

if((Test-Path $core1) -and (Test-Path $core2) -and (Test-Path $core3)){
  Write-Host "[C_PHASE] OK: core artifacts exist (main path)" -ForegroundColor Green
} else {
  Write-Host "[C_PHASE] WARN: core artifacts missing -> try fallback salvage from tickets_long_worldline" -ForegroundColor Yellow

  if(!(Test-Path $salv)){ Die "NG: fallback script missing: $salv" }

  # locate a tickets_long* to salvage from (prefer worldline outputs)
  $cand = @(
    (Join-Path $RUN "tickets_long_worldline.csv"),
    (Join-Path $RUN "tickets_long.csv")
  )
  # also search WORLDLINEONLY sibling dirs
  $sib = Get-ChildItem $RUNS -Directory | Where-Object {$_.Name -like ("C_OUT_FIXED_" + $Date + "*WORLDLINE*")} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if($sib){
    $cand += (Join-Path $sib.FullName "tickets_long_worldline.csv")
    $cand += (Join-Path $sib.FullName "tickets_long.csv")
  }

  $tickets = $cand | Where-Object { Test-Path $_ } | Select-Object -First 1
  if(-not $tickets){
    Write-Host "[C_PHASE] Cannot find tickets_long*.csv to salvage from." -ForegroundColor Red
    Write-Host "[C_PHASE] Files under RunDir:" -ForegroundColor Red
    dir $RUN | Format-Table -AutoSize | Out-String | Write-Host
    if($sib){
      Write-Host ("[C_PHASE] Files under sibling worldline dir: " + $sib.FullName) -ForegroundColor Red
      dir $sib.FullName | Format-Table -AutoSize | Out-String | Write-Host
    }
    Die "NG: core artifacts missing and no tickets_long for fallback"
  }

  Write-Host ("[C_PHASE] Fallback tickets=" + $tickets) -ForegroundColor Cyan
  python $salv --tickets $tickets --run $RUN --cap $Cap --date $Date
  if($LASTEXITCODE -ne 0){ Die "NG: fallback salvage failed" }

  if(!(Test-Path $core1)){ Die "NG: fallback did not produce CAP10_core5_races.csv" }
  Write-Host "[C_PHASE] OK: core artifacts exist (fallback path)" -ForegroundColor Green
}

# --- Goal: display to console (no deadline dependency) ---
Write-Host ""
Write-Host "==== C_PHASE GOAL (Selected races to display) ====" -ForegroundColor Green
try{
  $df = Import-Csv $core1
  $show = $df | Select-Object -First 15
  $show | Format-Table -AutoSize | Out-String | Write-Host
  Write-Host ("OUT: " + $core1) -ForegroundColor Green
}catch{
  Write-Host ("[C_PHASE] Could not display races: " + $_.Exception.Message) -ForegroundColor Yellow
  Write-Host ("OUT: " + $core1) -ForegroundColor Yellow
}

Stop-Transcript | Out-Null

if($mainExit -ne 0){
  Write-Host ("[C_PHASE] NOTE: main runner exit=" + $mainExit + " (fallback may have been used)") -ForegroundColor Yellow
}
Write-Host ("[C_PHASE] Log saved: " + $log) -ForegroundColor Green
