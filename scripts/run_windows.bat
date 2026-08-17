@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

if not exist "logs" mkdir "logs" >nul 2>&1
set "BOOTLOG=logs\bootstrap.log"

> "%BOOTLOG%" echo [%date% %time%] Bootstrap started

echo ============================================================
echo   NovelAI Prompt Lab - Windows launcher
echo ============================================================
echo.
echo LM Studio is OPTIONAL for startup.
echo This window will stay open if anything fails.
echo.

set "PY_CMD="

where py >nul 2>&1
if not errorlevel 1 (
  py -3 -c "import sys; print(sys.executable)" >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3"
)

if not defined PY_CMD (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 set "PY_CMD=python"
  )
)

if not defined PY_CMD goto :no_python

%PY_CMD% -c "import sys; print('[OK] Python', sys.version.split()[0], '-', sys.executable)"
if errorlevel 1 goto :fail

if not exist ".venv\Scripts\python.exe" (
  echo [SETUP] Creating local virtual environment...
  >> "%BOOTLOG%" echo Creating venv
  %PY_CMD% -m venv ".venv"
  if errorlevel 1 goto :fail
)

set "VPY=.venv\Scripts\python.exe"

"%VPY%" -c "import gradio,httpx,pydantic,dotenv; assert gradio.__version__ == '6.5.1'" >nul 2>&1
if errorlevel 1 (
  echo [SETUP] Installing verified dependencies. First launch can take a few minutes...
  >> "%BOOTLOG%" echo Installing dependencies
  "%VPY%" -m pip install --disable-pip-version-check -r "requirements.lock.txt"
  if errorlevel 1 goto :fail
)

echo.
echo [START] Opening Gradio UI...
echo [INFO] If port 7860 is occupied, another free port will be selected.
echo [INFO] Detailed log: logs\startup.log
echo.
"%VPY%" -u "launcher.py"
set "APP_EXIT=%ERRORLEVEL%"

if "%APP_EXIT%"=="0" goto :done

echo.
echo [ERROR] Application exited with code %APP_EXIT%.
echo [ERROR] Open logs\startup.log and logs\bootstrap.log for details.
goto :fail_pause

:no_python
echo.
echo [ERROR] Python 3 was not found.
echo [ERROR] Install 64-bit Python 3.11, 3.12, or 3.13 and enable the Python Launcher.
>> "%BOOTLOG%" echo Python not found
goto :fail_pause

:fail
echo.
echo [ERROR] Setup/startup command failed with code %ERRORLEVEL%.
echo [ERROR] See the messages above and logs\bootstrap.log.

:fail_pause
echo.
pause
exit /b 1

:done
echo.
echo Application stopped normally.
pause
exit /b 0
