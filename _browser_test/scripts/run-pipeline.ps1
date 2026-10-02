param ()

$ErrorActionPreference = 'Stop'

Write-Host 'Browser test pipeline starting...'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$configPath = Join-Path $projectRoot 'config\stack.env.ps1'

if (-not (Test-Path $configPath)) {
  Write-Error "Environment file not found at $configPath. Copy config/stack.env.ps1.example to config/stack.env.ps1 and configure it."
  exit 1
}

. $configPath

Set-Location $projectRoot

# ── Pre-flight static scan: verify every spec uses the fixtures guard
#    (commands/workflows/verify) and contains actions + assertions.
Write-Host "Running pre-test static scan..."
npx tsx scripts/preTestScan.js
if ($LASTEXITCODE -ne 0) {
  Write-Warning "preTestScan reported issues; continuing to Playwright run."
}

$playwrightExitCode = 0
npx playwright test
$playwrightExitCode = $LASTEXITCODE

# Copy latest results to last-run.json for CI artifact stability
$resultsPath = Join-Path $projectRoot 'reports\run\results.json'
$lastRunPath = Join-Path $projectRoot 'reports\run\last-run.json'
if (Test-Path $resultsPath) {
  $reportsDir = Split-Path -Parent $lastRunPath
  if (-not (Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
  }
  Copy-Item -Path $resultsPath -Destination $lastRunPath -Force
  Write-Host "Copied results.json -> last-run.json"
} else {
  Write-Warning "results.json not found at $resultsPath; skipping last-run copy"
}

Write-Host "Browser test pipeline finished with exit code $playwrightExitCode"
exit $playwrightExitCode
