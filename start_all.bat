@echo off
echo ========================================================
echo Starting AI Certificate Verification System Full Stack
echo ========================================================

echo Launching Backend Server on http://127.0.0.1:8000 ...
start "Backend - FastAPI" cmd /k "cd /d "%~dp0backend" && if exist "..\.venv\Scripts\uvicorn.exe" ("..\.venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload) else (uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)"

echo Launching Frontend UI on http://localhost:5173 ...
start "Frontend - Vite Dev" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Both services launched in separate windows.
