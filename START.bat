@echo off
setlocal
cd /d "%~dp0"
call "scripts\run_windows.bat"
exit /b %ERRORLEVEL%
