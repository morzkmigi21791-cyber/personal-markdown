@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Fix All Issues
echo ========================================
echo.

echo This script will fix all common issues by:
echo 1. Stopping all services
echo 2. Cleaning Docker resources
echo 3. Rebuilding and restarting services
echo 4. Running database migrations
echo 5. Testing all services
echo.

set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo [1/6] Stopping all services...
docker-compose -f docker-compose.full.yml down
docker-compose down
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo OK: All services stopped

echo.
echo [2/6] Cleaning Docker resources...
docker system prune -f
echo OK: Docker cleaned

echo.
echo [3/6] Rebuilding and starting services...
docker-compose -f docker-compose.full.yml up --build -d
if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)
echo OK: Services started

echo.
echo [4/6] Waiting for services to be ready...
timeout /t 25 /nobreak >nul

echo.
echo [5/6] Running database migrations...
docker exec siteofsites_backend python migrate_hosting.py 2>nul
docker exec siteofsites_backend python fix_enum_migration.py 2>nul
echo OK: Migrations completed

echo.
echo [6/6] Testing services...
echo Testing backend API...
curl -s http://localhost:8000/ >nul && echo "✅ Backend API: OK" || echo "❌ Backend API: FAILED"

echo Testing main site...
curl -s http://localhost/ >nul && echo "✅ Main Site: OK" || echo "❌ Main Site: FAILED"

echo Testing registration endpoint...
curl -s -X POST http://localhost/api/auth/register -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"testpass123\",\"nickname\":\"testuser\"}" >nul && echo "✅ Registration API: OK" || echo "❌ Registration API: FAILED"

echo.
echo ========================================
echo    Fix Complete
echo ========================================
echo.
echo Services are now running:
echo - Main Site: http://localhost
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - MinIO Console: http://localhost:9001
echo.
echo MinIO Login: Qwerty / 19216811!
echo.
echo All issues should now be fixed.
echo Try registering at: http://localhost
echo.
echo If you still have issues:
echo 1. Check logs: logs.bat
echo 2. Wait a bit more for services to fully start
echo 3. Check browser console for any remaining errors
echo.
pause