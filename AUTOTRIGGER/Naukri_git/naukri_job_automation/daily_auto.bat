@echo off
setlocal

:: Get the directory of the script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ==================================================
echo Naukri Daily Auto Run
echo ==================================================

:: Check for .venv
if not exist ".venv" (
    echo Error: Virtual environment .venv not found.
    echo Please run setup first.
    pause
    exit /b 1
)

:: Run daily auto: Update profile + Early access + Apply 50 jobs
echo Starting daily automation...
".venv\Scripts\python.exe" -m src.main auto --max-jobs 50 --no-headless

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong. Check the logs above.
    pause
) else (
    echo.
    echo Daily run completed successfully!
    timeout /t 10
)
