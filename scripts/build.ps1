$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
& .venv/Scripts/python.exe -m unittest discover -s tests -v
if($LASTEXITCODE -ne 0){throw 'Tests failed'}
& .venv/Scripts/python.exe scripts/make_icon.py
if($LASTEXITCODE -ne 0){throw 'Icons failed'}
& .venv/Scripts/python.exe -m PyInstaller --noconfirm PrismPixel.spec
if($LASTEXITCODE -ne 0){throw 'Build failed'}
Copy-Item README.md,THIRD_PARTY_NOTICES.md -Destination dist/PrismPixel -Force
Copy-Item -LiteralPath docs -Destination dist/PrismPixel -Recurse -Force
& .venv/Scripts/python.exe scripts/collect_licenses.py
if($LASTEXITCODE -ne 0){throw 'License collection failed'}
