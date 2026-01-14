Param(
  [Parameter(Mandatory=$true)][string]$WhatIfRoot,
  [Parameter(Mandatory=$true)][string]$OutCsv
)

# これはあなたの作業です
$root = (Get-Location).Path
$py = Join-Path $root "tools\preflight_check_whatif.py"

if(!(Test-Path $py)){
  Write-Error "missing: $py"
  exit 1
}

python $py --whatif-root $WhatIfRoot --out-csv $OutCsv

if($LASTEXITCODE -ne 0){
  Write-Error "preflight failed (python exitcode=$LASTEXITCODE)"
  exit $LASTEXITCODE
}

Write-Host "Done. Wrote: $OutCsv"
Write-Host "Summary: " ([IO.Path]::ChangeExtension($OutCsv,$null) + "_summary.txt")
