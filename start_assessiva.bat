
@echo off
title Assessiva Launcher

echo Starting Assessiva Backend...
start "Assessiva Backend" /D "%~dp0backend" cmd /k ""%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --reload"

echo Starting Assessiva Frontend...
start "Assessiva Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo Assessiva startup commands sent!
echo Frontend: http://localhost:5173
echo Backend: http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
