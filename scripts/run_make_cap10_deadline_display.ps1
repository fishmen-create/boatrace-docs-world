param(
  [Parameter(Mandatory=$true)][string]$Date,
  [Parameter(Mandatory=$true)][string]$RunDir
)

$ROOT="C:\work\boatrace"
$script = Join-Path $ROOT "scripts\make_cap10_deadline_display.py"
$races  = Join-Path $RunDir "CAP10_core5_races.csv"

if(!(Test-Path $script)){ throw "script not found: $script" }
if(!(Test-Path $races)){ throw "races not found: $races" }

Write-Host ("[deadline_display] Date=" + $Date) -ForegroundColor Cyan
Write-Host ("[deadline_display] RunDir=" + $RunDir) -ForegroundColor Cyan

python $script --date $Date --races $races --outdir $RunDir --root $ROOT
if($LASTEXITCODE -ne 0){
  throw "NG: deadline display generation failed. See output above."
}

# check outputs
$outCsv = Join-Path $RunDir "CAP10_core5_races_deadline_sorted.csv"
$outMd  = Join-Path $RunDir "CAP10_core5_deadline_list.md"
if(!(Test-Path $outCsv) -or !(Test-Path $outMd)){
  throw "NG: outputs not found: $outCsv / $outMd"
}

Write-Host "OK: display outputs generated" -ForegroundColor Green
Write-Host ("OUT_CSV=" + $outCsv) -ForegroundColor Green
Write-Host ("OUT_MD =" + $outMd) -ForegroundColor Green
