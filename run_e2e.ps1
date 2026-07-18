$root = "D:\Projects\10- E-COMMERCE WEBSITE\zozi"
$python = "$root\backend\.venv\Scripts\python.exe"

# Kill leftover processes
netstat -ano | Select-String ":8000 |:3000 " | ForEach-Object {
    $parts = $_ -split '\s+'
    $procId = $parts[-1]
    if ($procId -match '^\d+$' -and $procId -ne '0') { taskkill /F /PID $procId 2>$null }
}
Start-Sleep -Seconds 3

# Start backend
$env:BACKEND_PORT = "8000"
$be = Start-Process -FilePath $python -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning" -WorkingDirectory "$root\backend" -PassThru -WindowStyle Hidden

# Start frontend
$fe = Start-Process -FilePath "npx.cmd" -ArgumentList "next dev --hostname localhost --port 3000" -WorkingDirectory "$root\frontend\web_app" -PassThru -WindowStyle Hidden

Write-Host "Backend PID: $($be.Id), Frontend PID: $($fe.Id)"

# Wait for both
for ($i = 0; $i -lt 45; $i++) {
    $bk = $false; $ft = $false
    try { $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; if ($r.StatusCode -eq 200) { $bk = $true } } catch {}
    try { $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; if ($r.StatusCode -in @(200,304,307)) { $ft = $true } } catch {}
    if ($bk -and $ft) { Write-Host "Both ready after ${i}s"; break }
    if ($i -eq 0) { Start-Sleep -Seconds 8 } elseif ($i -lt 8) { Start-Sleep -Seconds 2 } else { Start-Sleep -Seconds 3 }
}
if (-not $bk) { throw "Backend not started" }
if (-not $ft) { throw "Frontend not started" }

# Run e2e tests
Write-Host "=== Running Playwright E2E Tests ==="
Set-Location "$root\frontend\web_app"
npx playwright test --reporter=list 2>&1
$exitCode = $LASTEXITCODE
Write-Host "E2E tests exited with code: $exitCode"

# Cleanup
Stop-Process -Id $be.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $fe.Id -Force -ErrorAction SilentlyContinue
exit $exitCode
