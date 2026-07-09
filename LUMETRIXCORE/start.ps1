Set-Location -Path $PSScriptRoot
Write-Host "=== LumetrixCore - arranque local ===" -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "[ERROR] Instala Python 3.11+ desde https://www.python.org/downloads/ (marca 'Add to PATH')." -ForegroundColor Red
  Read-Host "Enter para salir"; exit 1
}
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt
if (-not (Test-Path .env)) { python bootstrap_env.py }
Start-Process "http://localhost:8000"
Write-Host "=== http://localhost:8000  (Ctrl+C para detener) ===" -ForegroundColor Green
uvicorn app.main:app --reload --port 8000
