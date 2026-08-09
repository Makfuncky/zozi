$ErrorActionPreference = "Stop"
$logFile = Join-Path (Split-Path -Parent $PSCommandPath) "server.log"
$venv = Join-Path (Split-Path -Parent $PSCommandPath) "venv"
$python = Join-Path $venv "Scripts/python.exe"

$env:PYTHONUNBUFFERED = "1"

& $python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning 2>&1 | Tee-Object -FilePath $logFile
