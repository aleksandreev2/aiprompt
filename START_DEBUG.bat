@echo off
setlocal
cd /d "%~dp0"
echo Running diagnostics...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -u "scripts\diagnose.py"
) else (
  where py >nul 2>&1 && (py -3 -u "scripts\diagnose.py") || python -u "scripts\diagnose.py"
)
echo.
pause
