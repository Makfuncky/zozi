param(
  # Optional Playwright args, e.g. -Grep 'admin' or -Project chromium
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$PlaywrightArgs
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$configPath = Join-Path $projectRoot 'config\stack.env.ps1'

if (-not (Test-Path $configPath)) {
  if (Test-Path (Join-Path $projectRoot 'config\stack.env.ps1.example')) {
    Copy-Item (Join-Path $projectRoot 'config\stack.env.ps1.example') $configPath
    Write-Warning "Created $configPath from the example. Replace the placeholder secrets before running."
  } else {
    Write-Error "Environment file not found at $configPath and no .example to copy from."
    exit 1
  }
}

. $configPath

# playwright.config.ts reads API_BASE_URL / WEB_BASE_URL; stack.env.ps1 may only
# define BACKEND_URL / FRONTEND_URL. Bridge the two so there is one source of truth.
if (-not $env:API_BASE_URL -and $env:BACKEND_URL) { $env:API_BASE_URL = $env:BACKEND_URL }
if (-not $env:WEB_BASE_URL -and $env:FRONTEND_URL) { $env:WEB_BASE_URL = $env:FRONTEND_URL }

# One id per run so evidence accumulates instead of overwriting.
if (-not $env:RUN_ID) { $env:RUN_ID = (Get-Date).ToString('yyyyMMdd-HHmmss') }
Write-Host "Run id: $env:RUN_ID"

Set-Location $projectRoot

Write-Host '-- Static pre-flight scan ---------------------------------'
node scripts\preTestScan.mjs
if ($LASTEXITCODE -ne 0) {
  Write-Error 'preTestScan found blocking issues (broken or out-of-scope imports). Fix them before running Playwright.'
  exit 1
}

Write-Host ''
Write-Host '-- Playwright run -----------------------------------------'
$playwrightExitCode = 0
if ($PlaywrightArgs -and $PlaywrightArgs.Count -gt 0) {
  npx playwright test @PlaywrightArgs
} else {
  npx playwright test
}
$playwrightExitCode = $LASTEXITCODE

# Freeze the run summary so CI can diff against the previous run.
$resultsPath = Join-Path $projectRoot 'reports\run\results.json'
$lastRunPath = Join-Path $projectRoot 'reports\run\last-run.json'
if (Test-Path $resultsPath) {
  New-Item -ItemType Directory -Path (Split-Path -Parent $lastRunPath) -Force | Out-Null
  Copy-Item -Path $resultsPath -Destination $lastRunPath -Force
  Write-Host "Copied reports\run\results.json -> last-run.json"
} else {
  Write-Warning 'results.json not found; skipping last-run.json snapshot.'
}

# Build the browsable evidence gallery for this run.
Write-Host ''
Write-Host '-- Evidence gallery --------------------------------------'
node scripts\build-evidence-index.mjs $env:RUN_ID
if ($LASTEXITCODE -eq 0) {
  Write-Host "Open evidence\$env:RUN_ID\index.html"
} else {
  Write-Warning 'Evidence gallery could not be built (no evidence captured?).'
}

Write-Host "Pipeline finished with exit code $playwrightExitCode"
exit $playwrightExitCode