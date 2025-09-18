@echo off
echo ========================================
echo    Site of Sites - Quick Start
echo ========================================
echo.

echo 1. Starting Backend...
start "Backend" cmd /k "cd backend && python run.py"

echo 2. Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo ✅ Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
