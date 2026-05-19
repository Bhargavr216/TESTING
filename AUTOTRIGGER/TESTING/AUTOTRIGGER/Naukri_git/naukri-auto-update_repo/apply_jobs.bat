@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
set "DEFAULT_MAX_JOBS=5"
set "MAX_JOBS=%~1"

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

echo ============================================
echo           Naukri Apply Launcher
echo ============================================
echo.
echo This will open the browser and start applying jobs.
echo Make sure your config/profile.yaml and credentials are ready.
echo.

if not defined MAX_JOBS set /p "MAX_JOBS=How many jobs do you want to apply for? [%DEFAULT_MAX_JOBS%]: "
if "%MAX_JOBS%"=="" set "MAX_JOBS=%DEFAULT_MAX_JOBS%"

echo %MAX_JOBS%| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo.
    echo Invalid number: %MAX_JOBS%
    echo Please enter a whole number like 1, 5, or 10.
    pause
    popd >nul
    exit /b 1
)

echo.
echo Starting apply flow with max jobs = %MAX_JOBS%
echo Command:
echo %PYTHON_EXE% -m src.main apply --max-jobs %MAX_JOBS% --no-headless
echo.

"%PYTHON_EXE%" -m src.main apply --max-jobs %MAX_JOBS% --no-headless
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Apply flow finished.
) else (
    echo Apply flow ended with exit code %EXIT_CODE%.
)

pause
popd >nul
endlocal
exit /b %EXIT_CODE%
