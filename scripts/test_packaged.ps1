param([string]$Executable='')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
if (-not $Executable) { $Executable=Join-Path $projectRoot 'dist\PrismPixel\PrismPixel.exe' }
$resultDir=Join-Path $projectRoot ('validation\packaged_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
$previousPlatform=$env:QT_QPA_PLATFORM
try {
    $env:QT_QPA_PLATFORM='offscreen'
    $env:PRISM_PIXEL_CONFIG=Join-Path $resultDir 'settings.ini'
    $taskProcess=Start-Process -FilePath $Executable -ArgumentList @('--smoke-test', ('"'+$resultDir+'"')) -WindowStyle Hidden -PassThru
    if (-not $taskProcess.WaitForExit(100000)) { $taskProcess.Kill(); throw 'Packaged smoke test timed out.' }
    if ($taskProcess.ExitCode -ne 0) { throw "Packaged application exited with $($taskProcess.ExitCode)." }
    $resultPath=Join-Path $resultDir 'result.json'
    $result=Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
    if (-not $result.ok) { throw 'Packaged smoke test reported failure.' }
    Get-Content -LiteralPath $resultPath
    Write-Host "Screenshot: $resultDir\packaged_window.png"
} finally { $env:QT_QPA_PLATFORM=$previousPlatform; Remove-Item Env:\PRISM_PIXEL_CONFIG -ErrorAction SilentlyContinue }
