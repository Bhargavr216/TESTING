@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
set "HOST=127.0.0.1"
set "PORT=8765"
set "URL=http://%HOST%:%PORT%/"

pushd "%SCRIPT_DIR%" >nul

if not exist "%PYTHON_EXE%" (
    echo Could not find Python at:
    echo %PYTHON_EXE%
    echo.
    echo Create the virtual environment first, then install project dependencies.
    pause
    popd >nul
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    start "" /min "%PYTHON_EXE%" -m src.main reports-ui --host %HOST% --port %PORT% --no-browser

    powershell -NoProfile -ExecutionPolicy Bypass -Command "$url='%URL%'; $ready=$false; 1..20 | ForEach-Object { try { Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2 | Out-Null; $ready=$true; break } catch { Start-Sleep -Seconds 1 } }; if (-not $ready) { exit 1 }"
    if errorlevel 1 (
        echo The reports dashboard did not start in time.
        echo Please run this file again or start it manually.
        pause
        popd >nul
        exit /b 1
    )
)

start "" "%URL%"

popd >nul
endlocal
exit /b 0
