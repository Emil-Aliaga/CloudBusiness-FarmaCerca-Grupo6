@echo off
set ROOT=%~dp0

start "FarmaCerca Backend" cmd /k "cd /d "%ROOT%backend" && run_local.bat"

echo Esperando a que el backend responda...
:wait_backend
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto wait_backend
)

echo Backend listo.
start "FarmaCerca Frontend" cmd /k "cd /d "%ROOT%frontend" && run_local.bat"
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5500
