@echo off
echo ========================================================
echo Starting AI Certificate Verification System Full Stack
echo ========================================================

echo Freeing port 8000 from orphan processes...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo Launching Backend Server on http://0.0.0.0:8000 ...
start "Backend - FastAPI Resilient" cmd /k "cd /d "%~dp0backend" && if exist "%~dp0.venv\Scripts\python.exe" ("%~dp0.venv\Scripts\python.exe" run_server.py) else if exist "..\.venv\Scripts\python.exe" ("..\.venv\Scripts\python.exe" run_server.py) else (python run_server.py)"

echo Launching Frontend UI on http://localhost:5173 ...
start "Frontend - Vite Dev" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Both services launched in separate windows.
