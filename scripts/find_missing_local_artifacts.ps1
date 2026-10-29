# Read-only local discovery; no copying/upload, no recursive content inspection.
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\find_missing_local_artifacts.ps1
param([string]$SourceRoot = "$HOME\OneDrive - UTAD\dados\mcabral\LaTeX\Discover Internet of Things\out2026\testesV2")
$ErrorActionPreference = 'Stop'
Write-Host '===== OPTIONAL LOCAL ARTEFACT DISCOVERY (READ ONLY) ====='
Write-Host "ROOT=$SourceRoot"
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) { throw 'SOURCE_ROOT_NOT_FOUND' }
$names = @('policy_observations.csv','terminal_ledger.csv','Processed_Network_dataset.zip')
$found = New-Object System.Collections.Generic.List[object]
foreach ($name in $names) {
  Get-ChildItem -LiteralPath $SourceRoot -Recurse -File -Filter $name -ErrorAction SilentlyContinue | ForEach-Object {
    $found.Add([pscustomobject]@{Name=$_.Name;Bytes=$_.Length;Path=$_.FullName})
  }
}
Get-ChildItem -LiteralPath $SourceRoot -Recurse -File -Include '*d6*.joblib','*d6*.pkl' -ErrorAction SilentlyContinue | ForEach-Object {
  $found.Add([pscustomobject]@{Name=$_.Name;Bytes=$_.Length;Path=$_.FullName})
}
$found | Sort-Object Name,Path | Format-Table -Wrap | Out-String -Width 250 | Write-Host
Write-Host "FOUND=$($found.Count)"
Write-Host 'LARGE_FILES_READ=NO'
Write-Host 'SOURCE_MODIFIED=NO'
Write-Host 'Review any full local paths before sharing externally.'
