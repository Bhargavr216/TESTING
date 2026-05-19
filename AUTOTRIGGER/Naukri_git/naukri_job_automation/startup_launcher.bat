@echo off
setlocal

set "PROJECT_DIR=%NAUKRI_AUTOMATION_HOME%"
if "%PROJECT_DIR: =%"=="" set "PROJECT_DIR="
if not defined PROJECT_DIR (
  for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NAUKRI_AUTOMATION_HOME 2^>nul ^| find /i "NAUKRI_AUTOMATION_HOME"') do set "PROJECT_DIR=%%b"
)
if not defined PROJECT_DIR (
  echo [%date% %time%] NAUKRI_AUTOMATION_HOME is not set.>> "%TEMP%\\naukri_startup_launcher.log"
  echo [%date% %time%] Tip: run install_startup_launcher.bat and then sign out/in or restart Explorer.>> "%TEMP%\\naukri_startup_launcher.log"
  exit /b 1
)

if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

if not exist "%PROJECT_DIR%\\daily_auto_hidden.vbs" (
  echo [%date% %time%] Missing "%PROJECT_DIR%\\daily_auto_hidden.vbs">> "%TEMP%\\naukri_startup_launcher.log"
  exit /b 1
)

:: Run hidden (VBS calls daily_auto.bat which writes logs under %PROJECT_DIR%\\logs)
wscript.exe "%PROJECT_DIR%\\daily_auto_hidden.vbs"
exit /b %ERRORLEVEL%





