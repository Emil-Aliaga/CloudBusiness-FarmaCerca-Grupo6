@echo off
echo Restaurando datos iniciales de FarmaCerca...
curl -X POST -L http://127.0.0.1:8000/demo/reset
echo.
echo Listo. Actualiza el navegador.
pause
