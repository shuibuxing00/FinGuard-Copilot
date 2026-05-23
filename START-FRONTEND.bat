@echo off
cd /d "%~dp0\frontend"
set PATH=%~dp0tools\node-portable\node-v22.16.0-win-x64;%PATH%
call npm run dev
pause
