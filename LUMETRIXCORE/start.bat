@echo off
cd /d %~dp0
echo === LumetrixCore - arranque local ===
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No encuentro Python. Instala Python 3.11+ desde https://www.python.org/downloads/
  echo         y marca la casilla "Add Python to PATH" durante la instalacion.
  pause & exit /b 1
)
if not exist .venv (
  echo Creando entorno virtual...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Instalando dependencias (la primera vez tarda un poco)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if not exist .env ( python bootstrap_env.py )
echo.
echo === Abriendo http://localhost:8000  (Ctrl+C para detener) ===
start "" http://localhost:8000
uvicorn app.main:app --reload --port 8000
pause
