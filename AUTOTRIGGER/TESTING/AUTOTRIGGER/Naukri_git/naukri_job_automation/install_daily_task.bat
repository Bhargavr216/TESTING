@echo off
setlocal

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "TASK_NAME=NaukriDailyAuto"
set "DAILY_TIME=10:00"

echo ==================================================
echo Installing Windows scheduled task: %TASK_NAME%
echo Project: "%PROJECT_DIR%"
echo Daily time: %DAILY_TIME% (local time)
echo ==================================================
echo.

:: Persist project dir for Startup/Task-Scheduler use
setx NAUKRI_AUTOMATION_HOME "%PROJECT_DIR%" >nul 2>&1

:: Create / update a scheduled task (Logon + Daily) under the current user,
:: without storing your password (InteractiveToken).
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$taskName='%TASK_NAME%';" ^
  "$projectDir='%PROJECT_DIR%';" ^
  "$dailyTime='%DAILY_TIME%';" ^
  "$vbs=Join-Path $projectDir 'daily_auto_hidden.vbs';" ^
  "if (-not (Test-Path $vbs)) { throw ('Missing file: ' + $vbs) }" ^
  "$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('\"' + $vbs + '\"');" ^
  "$user = ($env:USERDOMAIN + '\' + $env:USERNAME);" ^
  "$triggers = @(" ^
  "  (New-ScheduledTaskTrigger -AtLogOn -User $user -RandomDelay (New-TimeSpan -Minutes 1))," ^
  "  (New-ScheduledTaskTrigger -Daily -At ([datetime]::Parse($dailyTime)) -RandomDelay (New-TimeSpan -Minutes 10))" ^
  ");" ^
  "$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 3);" ^
  "$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType InteractiveToken -RunLevel Highest;" ^
  "Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Force | Out-Null;" ^
  "Write-Host ('Installed/updated task: ' + $taskName);"

if errorlevel 1 (
  echo.
  echo Failed to install the scheduled task.
  echo Try running this file once as Administrator, or check PowerShell ScheduledTasks availability.
  exit /b 1
)

echo.
echo Done.
echo - Task Scheduler: %TASK_NAME%
echo - It runs at logon and daily at %DAILY_TIME%
echo - Logs are written under: "%PROJECT_DIR%\\logs"
echo - Daily run is guarded to run once/day (see "%PROJECT_DIR%\\data\\daily_auto_last_run.csv")
echo.
exit /b 0


