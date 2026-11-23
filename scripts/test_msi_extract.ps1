param([string]$Version='0.1.0')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$msi=Join-Path $projectRoot ('releases\PrismPixel-'+$Version+'-x64.msi')
$target=Join-Path $projectRoot ('validation\extract_'+$Version+'_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $target -Force | Out-Null
$commandKey='HKLM:\Software\Classes\*\shell\PrismPixel\command'
$before=if (Test-Path -LiteralPath $commandKey) { (Get-Item -LiteralPath $commandKey).GetValue('') } else { '' }
$process=Start-Process msiexec.exe -ArgumentList @('/a',('"'+$msi+'"'),'/qn',('TARGETDIR="'+$target+'"'),'/L*v',('"'+$target+'\extract.log"')) -WindowStyle Hidden -PassThru
$process.WaitForExit()
if ($process.ExitCode -ne 0) { throw "MSI extraction failed: $($process.ExitCode)" }
$executables=@(Get-ChildItem -LiteralPath $target -Filter PrismPixel.exe -Recurse)
if ($executables.Count -ne 1) { throw 'Expected one extracted application.' }
& scripts/test_packaged.ps1 -Executable $executables[0].FullName
$installer=New-Object -ComObject WindowsInstaller.Installer
$db=$installer.OpenDatabase($msi,0)
$view=$db.OpenView('SELECT `Key`, `Value` FROM `Registry`')
$view.Execute()
$contextFound=$false
while($record=$view.Fetch()) {
    if($record.StringData(1) -eq 'Software\Classes\*\shell\PrismPixel\command') {
        if($record.StringData(2) -ne '"[INSTALLFOLDER]PrismPixel.exe" --shell "%1"'){throw 'Incorrect shell command'}
        $contextFound=$true
    }
}
$view.Close()
if(-not $contextFound){throw 'Missing context menu registration'}
$after=if (Test-Path -LiteralPath $commandKey) { (Get-Item -LiteralPath $commandKey).GetValue('') } else { '' }
if ($before -ne $after) { throw 'Existing context menu changed unexpectedly.' }
@{ok=$true;version=$Version;checks=@('MSI payload extraction','packaged startup and image conversion','MSI context-menu command verified','existing installation unchanged')} | ConvertTo-Json | Set-Content (Join-Path $target 'result.json') -Encoding UTF8
Get-Content (Join-Path $target 'result.json')
