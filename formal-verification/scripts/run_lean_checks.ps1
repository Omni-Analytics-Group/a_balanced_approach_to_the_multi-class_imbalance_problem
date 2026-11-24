# Run in PowerShell 7 / Windows PowerShell from the original repository root:
#   powershell -ExecutionPolicy Bypass -File formal-verification/scripts/run_lean_checks.ps1
# Writes diagnostic logs to formal-verification/results/; no code changes.

$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$results = Join-Path $project 'results'
New-Item -ItemType Directory -Force -Path $results | Out-Null
Set-Location $project

Write-Host 'LEAN ENVIRONMENT:'
Get-Command lake -ErrorAction Stop | Out-Host
$env:LEAN_NUM_THREADS = '2'

function Run-Check($label, [string] $cmdline) {
    Write-Host "`n=== $label ===" -ForegroundColor Cyan
    $log = Join-Path $results "$label.log"
    & cmd.exe /c "$cmdline 2>&1" | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    Write-Host "Exit code: $code; log: $log"
    if ($code -ne 0) {
        Write-Warning "$label failed. Continue collecting remaining diagnostic logs."
    }
    return $code
}

$update = Run-Check '00-update' 'lake update'
if ($update -ne 0) { Write-Warning 'lake update failed; check network/toolchain.' }
$cache = Run-Check '01-cache' 'lake exe cache get'
$core = Run-Check '02-core' 'lake build MosleyCBA.Core'
$props = Run-Check '03-properties' 'lake build MosleyCBA.Properties'
$examples = Run-Check '04-examples' 'lake build MosleyCBA.Examples'
$full = Run-Check '05-full-build' 'lake build'
if ($full -eq 0) {
    $axioms = Run-Check '06-axiom-audit' 'lake env lean MosleyCBA/AxiomAudit.lean'
} else {
    Write-Host 'Skipping axiom audit because full build failed.'
}
Set-Location (Split-Path $project -Parent)
python formal-verification/scripts/verify_numeric.py --output formal-verification/results/numeric_checks.json
Write-Host "`nPlease return the logs under: $results" -ForegroundColor Green
