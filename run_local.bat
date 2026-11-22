@echo off
set ROOT=%~dp0
start "FarmaCerca Backend" cmd /k "cd /d "%ROOT%backend" && run_local.bat"
timeout /t 4 /nobreak >nul
start "FarmaCerca Frontend" cmd /k "cd /d "%ROOT%frontend" && run_local.bat"
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5500
