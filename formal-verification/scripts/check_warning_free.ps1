# Run from anywhere on Windows with elan, Lake, and Mathlib already configured.
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $projectRoot
New-Item -ItemType Directory -Force 'results' | Out-Null

$targets = @('MosleyCBA.Core', 'MosleyCBA.Properties', 'MosleyCBA.Examples', 'MosleyCBA')
foreach ($target in $targets) {
    $logName = 'results/warning_free_' + $target.Replace('.', '_') + '.log'
    Write-Host "Checking $target (warnings treated as failures)..." -ForegroundColor Cyan
    & lake build --wfail $target 2>&1 | Tee-Object -FilePath $logName
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
        throw "Build failed for $target (exit $exit). Upload $logName for diagnosis."
    }
}

Write-Host 'Running axiom audit...' -ForegroundColor Cyan
& lake env lean MosleyCBA/AxiomAudit.lean 2>&1 |
    Tee-Object -FilePath 'results/warning_free_axiom_audit.log'
$exit = $LASTEXITCODE
if ($exit -ne 0) {
    throw "Axiom audit failed (exit $exit)."
}
$axiomLog = Get-Content 'results/warning_free_axiom_audit.log' -Raw
if ($axiomLog -match 'sorryAx|\bsorry\b') {
    throw 'Axiom audit contains sorry/sorryAx. Investigate before claiming complete verification.'
}
if ($axiomLog -match '(?m)^\s*warning:') {
    throw 'Axiom audit emitted a Lean warning; inspect the log.'
}
Write-Host 'PASS: All four builds produced no warnings; axiom audit found no sorryAx.' -ForegroundColor Green
