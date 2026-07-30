<#
.SYNOPSIS
    Zozi Backend — Time-Budgeted Test Runner (PowerShell)
.DESCRIPTION
    Runs pytest with sensible timeouts for the Zozi backend test suite.
    Handles the ~12s app import overhead and 45-60s per-test-file baseline.

.PARAMETER Path
    Run a specific test file/directory instead of all tests.

.PARAMETER Fast
    Skip @pytest.mark.integration tests (unit-only mode).

.PARAMETER Profile
    Show the 20 slowest test durations.

.PARAMETER List
    List all test files with timing estimates.

.EXAMPLE
    .\run_tests.ps1                   # Run all tests
    .\run_tests.ps1 -Fast             # Unit tests only
    .\run_tests.ps1 -Path tests/test_health.py
    .\run_tests.ps1 -Profile          # Show slow tests
#>

param(
    [string]$Path = "",
    [switch]$Fast,
    [switch]$Profile,
    [switch]$List
)

$ErrorActionPreference = "Stop"
$TIMEOUT_SECONDS = 180

# ── List mode ────────────────────────────────────────────────────────────────
if ($List) {
    Write-Host "=== Test files detected ===" -ForegroundColor Cyan
    Get-ChildItem -Path tests -Filter "test_*.py" -Recurse | Sort-Object Name | ForEach-Object {
        Write-Host "  $($_.Name)"
    }
    Write-Host ""
    Write-Host "=== Timing estimates ===" -ForegroundColor Cyan
    Write-Host "  Per file:          ~45-60s  (includes 12s app import)"
    Write-Host "  All tests:         ~60-90s  (session-scoped fixtures shared)"
    Write-Host "  With -Fast:        ~15-30s  (unit-only markers)"
    return
}

# ── Build pytest arguments ────────────────────────────────────────────────────
$pytestArgs = @("-x", "--tb=short", "-q", "--timeout=$TIMEOUT_SECONDS")

if ($Profile) {
    $pytestArgs += "--durations=20"
}

if ($Fast) {
    Write-Host "🔹 Fast mode: skipping @pytest.mark.integration tests" -ForegroundColor Yellow
    $pytestArgs += @("-m", "not integration")
}

if ($Path) {
    $pytestArgs += $Path
} else {
    # Run all test files
    $testFiles = Get-ChildItem -Path tests -Filter "test_*.py" -Recurse | Sort-Object Name
    $testFiles | ForEach-Object { $pytestArgs += $_.FullName }
}

# ── Run ──────────────────────────────────────────────────────────────────────
$cmd = "python -m pytest $($pytestArgs -join ' ')"
Write-Host "🔹 Running: $cmd" -ForegroundColor Green
Write-Host ""

$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
    Invoke-Expression $cmd
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Command failed: $_" -ForegroundColor Red
    $exitCode = 1
}
$sw.Stop()

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ ALL TESTS PASSED in $($sw.Elapsed.TotalSeconds.ToString('F1'))s" -ForegroundColor Green
} else {
    Write-Host "❌ TESTS FAILED (exit code $exitCode) in $($sw.Elapsed.TotalSeconds.ToString('F1'))s" -ForegroundColor Red
}
exit $exitCode
