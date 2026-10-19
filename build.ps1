# Wrist & Hand dossier: rebuild the Atlas and the PDF, then run every check. Stops at the first failure.
#   powershell -ExecutionPolicy Bypass -File build.ps1            (build + checks + link audit)
#   powershell -ExecutionPolicy Bypass -File build.ps1 -SkipLinks (no network link audit)
param([switch]$SkipLinks)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$env:PYTHONUTF8 = "1"
if (Test-Path "C:\Program Files\nodejs") {
    $env:PATH = "C:\Program Files\nodejs;$env:PATH"
}

python atlas/build_atlas.py
if ($LASTEXITCODE -ne 0) { throw "Atlas build failed (exit $LASTEXITCODE)" }

python tools/build_dossier.py
if ($LASTEXITCODE -ne 0) { throw "Dossier build or checks FAILED (exit $LASTEXITCODE) - read the FAIL list above" }

if (-not $SkipLinks) {
    python tools/check_links.py
    if ($LASTEXITCODE -ne 0) { throw "Link audit FAILED (exit $LASTEXITCODE)" }
}
Write-Host "BUILD OK - master_wrist_hand_dossier.pdf and index.html are up to date"
