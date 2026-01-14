param(
  [string]$ZipPath = ""
)

$ErrorActionPreference = "Stop"

$ROOT = "C:\work\boatrace"
$DOC  = Join-Path $ROOT "docs"
$LOG  = Join-Path $DOC  "PATCHLOG.md"

function Pick-LatestPatchZip {
  $dl = Join-Path $env:USERPROFILE "Downloads"
  $z = Get-ChildItem $dl -File -Filter "boatrace_*patch*.zip" -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Desc | Select-Object -First 1
  if (-not $z) { return $null }
  return $z.FullName
}

if (-not $ZipPath) {
  $ZipPath = Pick-LatestPatchZip
}
if (-not $ZipPath) { throw "patch zip not found. Put boatrace_*patch*.zip in Downloads or pass -ZipPath." }
if (-not (Test-Path $ZipPath)) { throw "ZIP not found: $ZipPath" }

Write-Host ("[apply_chat_patch] zip=" + $ZipPath)

# Extract to C:\ (zip is expected to contain work\boatrace\...)
Expand-Archive -Force -Path $ZipPath -DestinationPath "C:\"

# Ensure PATCHLOG exists
if (-not (Test-Path $LOG)) {
  New-Item -ItemType File -Path $LOG -Force | Out-Null
  Add-Content -Path $LOG -Encoding UTF8 -Value "# PATCHLOG`r`n`r`n## entries`r`n"
}

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LOG -Encoding UTF8 -Value ("- " + $ts + " applied: " + (Split-Path $ZipPath -Leaf))

# Optional: run mandatory docs guard if exists
$guard = Join-Path $DOC "mandatory_docs_guard.ps1"
if (Test-Path $guard) {
  Write-Host "[apply_chat_patch] running mandatory_docs_guard..." -ForegroundColor Cyan
  powershell -NoProfile -ExecutionPolicy Bypass -File $guard -DocsDir $DOC
}

Write-Host "[apply_chat_patch] OK" -ForegroundColor Green
