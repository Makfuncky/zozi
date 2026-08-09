@echo off
title ZOZI E-Commerce Platform Launcher
color 0A

echo.
echo ============================================================================
echo   ZOZI E-COMMERCE PLATFORM - DEVELOPMENT LAUNCHER
echo ============================================================================
echo.

REM Get the directory where this script is located
set "PROJECT_ROOT=%~dp0"

echo [INFO] Project Root: %PROJECT_ROOT%
echo.

REM ============================================================================
REM START BACKEND (FastAPI on port 8000)
REM ============================================================================
echo [1/3] Starting Backend (FastAPI on port 8000)...
if not exist "%PROJECT_ROOT%backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend\venv
    echo Please ensure venv exists in the backend folder.
    pause
    exit /b 1
)

REM Kill any leftover process on port 8000 before starting (robust parsing)
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr /C:":8000 " ^| findstr /C:"LISTENING"') do (
    if not "%%p"=="" if not "%%p"=="0" taskkill /F /PID %%p >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Start backend using run_server.py (handles SO_REUSEADDR, port 8000)
start "ZOZI Backend (port 8000)" cmd /k "cd /d "%PROJECT_ROOT%backend" & venv\Scripts\python.exe run_server.py"
echo [SUCCESS] Backend terminal opened on port 8000.
echo.

REM ============================================================================
REM HEALTH CHECK GATE
REM Wait until the backend actually answers /health before starting the
REM frontend. This removes the previous "timeout /t 4" race condition where
REM the frontend could launch before the API was ready, causing cascading
REM "Failed to fetch" errors on first load.
REM ============================================================================
echo [GATE] Waiting for backend health endpoint (http://127.0.0.1:8000/health)...
set "BACKEND_UP=0"
set "MAX_WAIT=60"
set "WAITED=0"

:healthloop
if %WAITED% geq %MAX_WAIT% goto healthfail
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health 2>nul | findstr /C:"200" >nul 2>&1
if not errorlevel 1 (
    set "BACKEND_UP=1"
    goto healthdone
)
timeout /t 2 /nobreak >nul
set /a WAITED+=2
goto healthloop

:healthfail
echo [ERROR] Backend did not become healthy within %MAX_WAIT% seconds.
echo         The backend terminal above may show the reason. Fix it, then re-run this launcher.
echo         (Frontend/mobile launchers skipped to avoid a broken startup.)
echo.
pause
exit /b 1

:healthdone
echo [OK] Backend healthy after ~%WAITED%s. Proceeding.
echo.

REM ============================================================================
REM START FRONTEND WEB (Next.js on port 3000)
REM ============================================================================
echo [2/3] Starting Frontend Web App (Next.js on port 3000)...
if not exist "%PROJECT_ROOT%frontend\web_app\package.json" (
    echo [ERROR] Frontend web app not found at frontend\web_app
    pause
    exit /b 1
)

start "ZOZI Frontend (port 3000)" cmd /k "cd /d "%PROJECT_ROOT%frontend\web_app" && npm run dev"
echo [SUCCESS] Frontend Web terminal opened on port 3000.
echo.

timeout /t 2 /nobreak >nul

REM ============================================================================
REM START FRONTEND MOBILE (Expo)
REM ============================================================================
echo [3/3] Checking Mobile App (Expo)...
if exist "%PROJECT_ROOT%frontend\mobile_app\package.json" (
    start "ZOZI Mobile (Expo)" cmd /k "cd /d "%PROJECT_ROOT%frontend\mobile_app" && npx expo start"
    echo [SUCCESS] Mobile App terminal opened.
) else (
    echo [INFO] Mobile app not found at frontend\mobile_app, skipping.
)
echo.

REM ============================================================================
REM DISPLAY INFO
REM ============================================================================
echo ============================================================================
echo   ZOZI E-COMMERCE PLATFORM IS LAUNCHING!
echo ============================================================================
echo.
echo   Frontend  (Web):      http://localhost:3000
echo   Backend API:          http://127.0.0.1:8000
echo   API Docs (Swagger):   http://127.0.0.1:8000/docs
echo   Mobile App (Expo):    http://localhost:19006  (or scan QR in terminal)
echo.
echo ============================================================================
echo   TEST ACCOUNTS — see scripts/testing/loadtests/README.md for credentials
echo   (Credentials are seeded by db/seed.py on first startup)
echo ============================================================================
echo.
echo ============================================================================
echo   INSTRUCTIONS
echo ============================================================================
echo   - Three separate terminal windows have been opened.
echo   - Do NOT close this main launcher window until you are done.
echo   - To stop the servers, press Ctrl+C in each terminal window.
echo.
echo ============================================================================
echo   HAPPY CODING WITH ZOZI!
echo ============================================================================
echo.

pause
