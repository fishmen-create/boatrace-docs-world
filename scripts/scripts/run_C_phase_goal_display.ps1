param(
  [Parameter(Mandatory=$true)][string]$Date
)

$ROOT = "C:\work\boatrace"
$RUNS = Join-Path $ROOT "runs"
$RUN  = Join-Path $RUNS ("C_OUT_FIXED_" + $Date)

$bat = Join-Path $ROOT "scripts\run_C_out_core5_cap10.bat"
$ps1 = Join-Path $ROOT "scripts\run_C_out_core5_cap10.ps1"
$disp = Join-Path $ROOT "scripts\run_make_cap10_deadline_display.ps1"

function Die($msg){
  Write-Host $msg -ForegroundColor Red
  exit 1
}

Write-Host ("[C_PHASE] Date=" + $Date) -ForegroundColor Cyan
Write-Host ("[C_PHASE] RunDir=" + $RUN) -ForegroundColor Cyan

# ---- Stage0: sanity (最低限) ----
if(!(Test-Path $RUNS)){ Die "NG: runs dir not found: $RUNS" }
if(!(Test-Path $disp)){ Die "NG: display runner not found: $disp" }

# b_files existence (BYYMMDD)
$b = Join-Path $ROOT "b_files"
if(!(Test-Path $b)){ Die "NG: b_files dir not found: $b" }
$yy = $Date.Substring(2,2); $mm=$Date.Substring(5,2); $dd=$Date.Substring(8,2)
$bf = Join-Path $b ("B{0}{1}{2}.TXT" -f $yy,$mm,$dd)
if(!(Test-Path $bf)){ Die "NG: B file not found: $bf  (Downloads→prepare_b_files_v2.py の対象)" }

# ---- Stage1: guard against WORLDLINE-ONLY dir (混入防止) ----
if(Test-Path $RUN){
  $has_cap10 = Test-Path (Join-Path $RUN "CAP10_core5_races.csv")
  $has_world = Test-Path (Join-Path $RUN "report_worldline.csv")
  if((!$has_cap10) -and $has_world){
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $bak = $RUN + "_WORLDLINEONLY_" + $ts
    Write-Host ("[C_PHASE] Detected WORLDLINE-only dir. Rename to: " + $bak) -ForegroundColor Yellow
    Rename-Item -LiteralPath $RUN -NewName (Split-Path $bak -Leaf)
  }
}

# ---- Stage2: run core5+cap10 (bat優先) ----
if(Test-Path $bat){
  Write-Host ("[C_PHASE] Run: " + $bat + " " + $Date) -ForegroundColor Cyan
  cmd /c "`"$bat`" $Date"
  if($LASTEXITCODE -ne 0){ Die "NG: run_C_out_core5_cap10.bat failed (exit=$LASTEXITCODE)" }
} elseif (Test-Path $ps1){
  Write-Host ("[C_PHASE] Run: " + $ps1) -ForegroundColor Cyan
  powershell -NoProfile -ExecutionPolicy Bypass -File $ps1 $Date
  if($LASTEXITCODE -ne 0){ Die "NG: run_C_out_core5_cap10.ps1 failed (exit=$LASTEXITCODE)" }
} else {
  Die "NG: neither run_C_out_core5_cap10.bat nor .ps1 found under scripts/"
}

# ---- Stage3: outputs must exist (core artifacts) ----
if(!(Test-Path $RUN)){ Die "NG: RunDir not created: $RUN" }

$core1 = Join-Path $RUN "CAP10_core5_races.csv"
$core2 = Join-Path $RUN "CAP10_core5_tickets_long.csv"
$core3 = Join-Path $RUN "CAP10_core5_meta.json"

if(!(Test-Path $core1) -or !(Test-Path $core2) -or !(Test-Path $core3)){
  Write-Host "NG: CAP10_core5 outputs missing. Files under RunDir:" -ForegroundColor Red
  dir $RUN | Format-Table -AutoSize | Out-String | Write-Host
  Die "NG: core artifacts not complete: $RUN"
}

Write-Host "[C_PHASE] OK: core artifacts exist" -ForegroundColor Green

# ---- Stage4: display (deadline sorted) ----
Write-Host ("[C_PHASE] Display: " + $disp) -ForegroundColor Cyan
powershell -NoProfile -ExecutionPolicy Bypass -File $disp -Date $Date -RunDir $RUN
if($LASTEXITCODE -ne 0){ Die "NG: deadline display failed" }

Write-Host "[C_PHASE] DONE: core + display completed" -ForegroundColor Green
Write-Host ("RunDir=" + $RUN) -ForegroundColor Green
