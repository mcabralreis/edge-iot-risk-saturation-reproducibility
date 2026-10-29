# Windows PowerShell 5.1 compatible, local archive check only.
# Read-only on scientific originals; only report TXT written to Downloads.
param([string]$RepositoryRoot = '')
$ErrorActionPreference = 'Stop'
$Report = Join-Path (Join-Path $HOME 'Downloads') 'DiscoverIoT_REPO_R6_smoke_report.txt'
$Out = New-Object 'System.Collections.Generic.List[string]'
function Log([string]$s) { [void]$Out.Add($s); Write-Host $s }
Log '===== DISCOVER IOT R6 REPOSITORY SMOKE CHECK ====='
Log 'MODE=ARCHIVE_VERIFICATION_ONLY'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
  $candidates = @(
    (Join-Path $HOME 'Downloads\edge-iot-risk-saturation-reproducibility_R6_DRAFT'),
    (Join-Path $HOME 'Downloads\edge-iot-risk-saturation-reproducibility_R6_DRAFT\edge-iot-risk-saturation-reproducibility_R6_DRAFT'),
    (Join-Path $HOME 'Downloads\edge-iot-risk-saturation-reproducibility'),
    (Join-Path $HOME 'Downloads\edge-iot-risk-saturation-reproducibility\edge-iot-risk-saturation-reproducibility'),
    (Get-Location).Path
  )
  foreach($c in $candidates) {
    if(Test-Path -LiteralPath (Join-Path $c 'verify_191bins.py') -PathType Leaf) { $RepositoryRoot=$c; break }
  }
}
if([string]::IsNullOrWhiteSpace($RepositoryRoot) -or -not (Test-Path -LiteralPath (Join-Path $RepositoryRoot 'verify_191bins.py') -PathType Leaf)) {
  Log 'REPOSITORY_ROOT=NOT_FOUND'
  Log 'ACTION=EXTRACT_R6_ZIP_AND_RETRY_OR_USE_-RepositoryRoot'
  $Out | Set-Content -LiteralPath $Report -Encoding UTF8
  exit 2
}
Log ('REPOSITORY_ROOT=' + $RepositoryRoot)
Log ('BASIC_EVIDENCE=' + (Test-Path -LiteralPath (Join-Path $RepositoryRoot 'evidence\P4_A1_matched_actions_191bins.csv')))
if(-not (Get-Command py -ErrorAction SilentlyContinue)) {
  Log 'PY_LAUNCHER=NOT_FOUND'
  $Out | Set-Content -LiteralPath $Report -Encoding UTF8
  exit 3
}
Log '===== PYTHON ARCHIVED-RESULT AUDIT ====='
$Res = @(& py -3 (Join-Path $RepositoryRoot 'verify_191bins.py') 2>&1 | Out-String -Stream)
$ExitCode=$LASTEXITCODE
foreach($line in $Res) { if(-not [string]::IsNullOrWhiteSpace($line)) { Log $line } }
Log ('VERIFY_EXIT_CODE=' + $ExitCode)
Log '===== OPTIONAL CONTENT SCAN ====='
$Res2 = @(& py -3 (Join-Path $RepositoryRoot 'scripts\verify_public_contents.py') 2>&1 | Out-String -Stream)
$ExitCode2=$LASTEXITCODE
foreach($line in $Res2) { if(-not [string]::IsNullOrWhiteSpace($line)) { Log $line } }
Log ('CONTENT_CHECK_EXIT_CODE=' + $ExitCode2)
Log 'SCIENTIFIC_EXECUTION=NO'
Log 'THIRD_PARTY_DATA_READ=NO'
Log 'ORIGINAL_SCIENTIFIC_FILES_MODIFIED=NO'
Log ('REPORT=' + $Report)
$Out | Set-Content -LiteralPath $Report -Encoding UTF8
if($ExitCode -ne 0 -or $ExitCode2 -ne 0) { exit 1 }
