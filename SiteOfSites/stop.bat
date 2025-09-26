@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Stop All Services
echo ========================================
echo.

echo Stopping all services...
echo.

echo [1/3] Stopping Docker services (MinIO + Nginx)...
docker-compose down
if errorlevel 1 (
    echo WARNING: Docker Compose not found, trying docker compose...
    docker compose down
    if errorlevel 1 (
        echo WARNING: Failed to stop Docker services
    ) else (
        echo OK: Docker services stopped
    )
) else (
    echo OK: Docker services stopped
)

echo.
echo [2/3] Stopping Backend server...
taskkill /f /im python.exe >nul 2>&1
if errorlevel 1 (
    echo INFO: Backend server was not running
) else (
    echo OK: Backend server stopped
)

echo.
echo [3/3] Stopping Frontend server...
taskkill /f /im node.exe >nul 2>&1
if errorlevel 1 (
    echo INFO: Frontend server was not running
) else (
    echo OK: Frontend server stopped
)

echo.
echo ========================================
echo    All services stopped successfully!
echo ========================================
echo.
echo To start services again, run start.bat
echo.
echo Press any key to close this window...
pause >nul
