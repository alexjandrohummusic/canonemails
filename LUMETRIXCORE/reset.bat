@echo off
cd /d %~dp0
if exist lumetrix.db (
  del lumetrix.db
  echo Base de datos reiniciada (lumetrix.db eliminada). Se recreara limpia al arrancar.
) else (
  echo No habia base de datos que reiniciar.
)
echo Ahora vuelve a ejecutar start.bat
pause
