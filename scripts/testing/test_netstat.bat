@echo on
set "NS_TEMP=%TEMP%\zozi_netstat.tmp"
netstat -an > "%NS_TEMP%"
find "8000" "%NS_TEMP%" >nul 2>&1
if %errorlevel% equ 0 (
    find "LISTENING" "%NS_TEMP%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [WARNING] Port 8000 is already in use. Backend might already be running.
        echo [INFO] Continuing with frontend startup...
    ) else (
        echo START_BACKEND=1
    )
) else (
    echo START_BACKEND=1
)
