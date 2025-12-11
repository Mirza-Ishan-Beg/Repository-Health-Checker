@echo off
REM run_automator_bg.bat  -- place in project root

REM ensure we run from the script folder
cd /d "%~dp0"

REM paths inside project root
SET "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
SET "SCRIPT_PATH=%~dp0Automator.py"
SET "LOG_PATH=%~dp0automator_run.log"

echo [%DATE% %TIME%] Launcher: starting background run >> "%LOG_PATH%"

REM verify files exist
if not exist "%VENV_PYTHON%" (
  echo [%DATE% %TIME%] ERROR: venv python not found: "%VENV_PYTHON%" >> "%LOG_PATH%"
  exit /b 2
)
if not exist "%SCRIPT_PATH%" (
  echo [%DATE% %TIME%] ERROR: script not found: "%SCRIPT_PATH%" >> "%LOG_PATH%"
  exit /b 3
)

REM start python in background (no window) and log output
start "" /B "%VENV_PYTHON%" "%SCRIPT_PATH%" >> "%LOG_PATH%" 2>&1

echo [%DATE% %TIME%] Launcher: start command issued. >> "%LOG_PATH%"
exit /b 0
