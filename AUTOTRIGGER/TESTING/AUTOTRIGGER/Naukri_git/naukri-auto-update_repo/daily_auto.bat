@echo off
setlocal

:: Get the directory of the script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ==================================================
echo Naukri Daily Auto Run (Update + Apply)
echo ==================================================

:: Check for .venv
if not exist ".venv" (
    echo Error: Virtual environment .venv not found.
    echo Please run setup first.
    pause
    exit /b 1
)

:: Step 1: Update Profile
echo Updating profile...
".venv\Scripts\python.exe" update_naukri.py --no-headless

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Profile update failed. Check the logs above.
    pause
    exit /b 1
)

echo.
echo Profile updated successfully!
echo.

:: Step 2: Apply to Jobs
echo Applying to jobs (50 jobs)...
".venv\Scripts\python.exe" -m src.main apply --max-jobs 50 --no-headless

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong during apply. Check the logs above.
    pause
) else (
    echo.
    echo Daily run completed successfully!
    timeout /t 10
)
