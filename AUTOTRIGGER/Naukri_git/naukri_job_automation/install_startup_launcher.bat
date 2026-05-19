@echo off
setlocal

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "STARTUP_DIR=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
set "TARGET=%STARTUP_DIR%\\NaukriStartupLauncher.bat"

echo ==================================================
echo Installing Windows Startup launcher
echo Project: "%PROJECT_DIR%"
echo Startup: "%STARTUP_DIR%"
echo ==================================================
echo.

:: Persist project dir so the Startup launcher can find the repo even if it lives in Startup folder
setx NAUKRI_AUTOMATION_HOME "%PROJECT_DIR%" >nul 2>&1

if not exist "%STARTUP_DIR%" (
  echo Error: Startup folder not found: "%STARTUP_DIR%"
  exit /b 1
)

copy /y "%PROJECT_DIR%\\startup_launcher.bat" "%TARGET%" >nul
if errorlevel 1 (
  echo Error: Failed to copy startup launcher to: "%TARGET%"
  exit /b 1
)

echo Done.
echo - Startup launcher: "%TARGET%"
echo - Logs on failure: "%%TEMP%%\\naukri_startup_launcher.log"
echo - Daily logs: "%PROJECT_DIR%\\logs"
echo.
echo Note: Startup items can be disabled by Windows. For best reliability, also run:
echo   "%PROJECT_DIR%\\install_daily_task.bat"
echo.
exit /b 0


