#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs the ZOZI mobile_app Playwright e2e suite.

.DESCRIPTION
    1. Validates the Expo web build (expo export) compiles.
    2. Starts the static web server (expo export --web dist).
    3. Runs `npx playwright test` against the web build with mobile-viewport emulation.
    4. Stops the server and exits with the same code as the test run.

    Honours $env:PW_BASE_URL (default http://localhost:8090), $env:PW_SKIP_BUILD,
    and $env:PW_SKIP_INSTALL to skip the heavy steps when the caller already ran them.
#>
[CmdletBinding()]
param(
    [string]$BaseUrl = $env:PW_BASE_URL,
    [switch]$SkipBuild = [bool]$env:PW_SKIP_BUILD,
    [switch]$SkipInstall = [bool]$env:PW_SKIP_INSTALL,
    [switch]$Headed,
    [string]$Grep
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$MobileApp = Join-Path $RepoRoot "frontend\mobile_app"
$Backend = Join-Path $RepoRoot "backend"
$WebDist = Join-Path $MobileApp "web-dist"
$LogDir = Join-Path $RepoRoot "_audit_results\logs"
$LogFile = Join-Path $LogDir "mobile_e2e.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
"" | Out-File -FilePath $LogFile -Encoding utf8

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    $line = "[$ts] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

if (-not $BaseUrl) { $BaseUrl = "http://localhost:8090" }
Write-Log "run-e2e starting (BaseUrl=$BaseUrl, SkipBuild=$SkipBuild, SkipInstall=$SkipInstall, Headed=$Headed)"

Push-Location $MobileApp
try {
    if (-not $SkipInstall) {
        Write-Log "Installing mobile_app dependencies (pnpm/npm ci)..."
        if (Test-Path "pnpm-lock.yaml") {
            & pnpm install --frozen-lockfile 2>&1 | ForEach-Object { Write-Log $_ }
        } else {
            & npm ci --legacy-peer-deps 2>&1 | ForEach-Object { Write-Log $_ }
        }
        if ($LASTEXITCODE -ne 0) { throw "Dependency install failed" }
    }

    if (-not $SkipBuild) {
        Write-Log "Exporting Expo web build to $WebDist ..."
        if (Test-Path $WebDist) { Remove-Item -Recurse -Force $WebDist }
        & npx expo export --platform web --output-dir "web-dist" 2>&1 | ForEach-Object { Write-Log $_ }
        if ($LASTEXITCODE -ne 0) { throw "expo export failed" }
    }

    if (-not (Test-Path $WebDist)) {
        throw "Web build directory $WebDist missing — run with -SkipBuild `$false to build it."
    }

    Write-Log "Starting static web server on $BaseUrl ..."
    $port = ([uri]$BaseUrl).Port
    if (-not $port) { $port = 8090 }
    $serverLog = Join-Path $LogDir "mobile_e2e_server.log"
    $serverProc = Start-Process -FilePath "node" `
        -ArgumentList @((Join-Path $ScriptDir "static-server.js"), $WebDist, $port) `
        -RedirectStandardOutput $serverLog -RedirectStandardError $serverLog `
        -NoNewWindow -PassThru
    Start-Sleep -Seconds 2

    # health check
    $healthy = $false
    for ($i = 0; $i -lt 15; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -lt 500) { $healthy = $true; break }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $healthy) {
        Write-Log "Server failed to become healthy at $BaseUrl"
        if ($serverProc -and -not $serverProc.HasExited) { $serverProc | Stop-Process -Force }
        throw "Static server did not respond"
    }
    Write-Log "Server healthy at $BaseUrl"

    $playwrightArgs = @("playwright", "test")
    if ($Grep) { $playwrightArgs += @("--grep", $Grep) }
    if ($Headed) { $playwrightArgs += "--headed" }
    $env:PW_BASE_URL = $BaseUrl

    Write-Log "Running: npx $($playwrightArgs -join ' ')"
    & npx @playwrightArgs 2>&1 | ForEach-Object { Write-Log $_ }
    $testExit = $LASTEXITCODE

    Write-Log "Playwright exit code: $testExit"
    return $testExit
}
finally {
    Pop-Location
    if ($serverProc -and -not $serverProc.HasExited) {
        Write-Log "Stopping static server (pid=$($serverProc.Id))"
        $serverProc | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    Write-Log "run-e2e complete"
    if ($testExit) { exit $testExit }
}
