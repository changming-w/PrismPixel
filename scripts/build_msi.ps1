param([string]$WixBin = $env:WIX_BIN)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not $WixBin -and (Test-Path -LiteralPath '.tools\wix314\candle.exe')) { $WixBin=Join-Path $projectRoot '.tools\wix314' }
if (-not $WixBin) { throw 'Pass -WixBin with the WiX 3.14.1 binaries directory, or set WIX_BIN.' }
$candle=Join-Path $WixBin 'candle.exe'
$light=Join-Path $WixBin 'light.exe'
if (-not (Test-Path -LiteralPath $candle)) { throw 'WiX candle.exe not found.' }
& .venv/Scripts/python.exe scripts/make_installer.py
if ($LASTEXITCODE -ne 0) { throw 'Manifest generation failed.' }
New-Item -ItemType Directory -Path releases -Force | Out-Null
& $candle -nologo -arch x64 -out build/installer/PrismPixel.wixobj build/installer/PrismPixel.wxs
if ($LASTEXITCODE -ne 0) { throw 'WiX compilation failed.' }
& $light -nologo -ext WixUIExtension -cultures:zh-CN -out releases/PrismPixel-0.1.0-x64.msi build/installer/PrismPixel.wixobj
if ($LASTEXITCODE -ne 0) { throw 'MSI linking or validation failed.' }
Write-Host 'Built releases/PrismPixel-0.1.0-x64.msi'
