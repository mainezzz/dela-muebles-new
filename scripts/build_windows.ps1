$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..

python -m pip install -e .[desktop,build]
pyinstaller --clean dela-furnfact.spec

Write-Host ""
Write-Host "Build completada."
Write-Host "Salida: dist\dela-furnfact\dela-furnfact.exe"
