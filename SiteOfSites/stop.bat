@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Universal Stop
echo ========================================
echo.

echo Choose what to stop:
echo [1] All Services (Docker + Local)
echo [2] Docker Services Only
echo [3] Local Services Only (Python + Node.js)
echo [4] Clean Everything (Docker + Local + Cleanup)
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto stop_all
if "%choice%"=="2" goto stop_docker
if "%choice%"=="3" goto stop_local
if "%choice%"=="4" goto clean_all
echo Invalid choice. Exiting...
pause
exit /b 1

:stop_all
echo.
echo Stopping all Site of Sites services...
echo.

echo [1/4] Stopping local processes...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
echo OK: Local processes stopped

echo [2/4] Stopping Docker Compose services...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

%DOCKER_COMPOSE_CMD% down >nul 2>&1
echo OK: Docker Compose services stopped

echo [3/4] Stopping Docker Full Stack services...
%DOCKER_COMPOSE_CMD% -f docker-compose.full.yml down >nul 2>&1
echo OK: Docker Full Stack services stopped

echo [4/4] All services stopped successfully!
goto end

:stop_docker
echo.
echo Stopping Docker services only...
echo.

echo [1/2] Stopping Docker Compose services...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

%DOCKER_COMPOSE_CMD% down >nul 2>&1
echo OK: Docker Compose services stopped

echo [2/2] Stopping Docker Full Stack services...
%DOCKER_COMPOSE_CMD% -f docker-compose.full.yml down >nul 2>&1
echo OK: Docker Full Stack services stopped

echo Docker services stopped successfully!
goto end

:stop_local
echo.
echo Stopping local services only...
echo.

echo [1/2] Stopping Node.js processes...
taskkill /f /im node.exe >nul 2>&1
echo OK: Node.js processes stopped

echo [2/2] Stopping Python processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
echo OK: Python processes stopped

echo Local services stopped successfully!
goto end

:clean_all
echo.
echo Cleaning everything (Docker + Local + Cleanup)...
echo.

echo [1/5] Stopping local processes...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
echo OK: Local processes stopped

echo [2/5] Stopping Docker Compose services...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

%DOCKER_COMPOSE_CMD% down >nul 2>&1
echo OK: Docker Compose services stopped

echo [3/5] Stopping Docker Full Stack services...
%DOCKER_COMPOSE_CMD% -f docker-compose.full.yml down >nul 2>&1
echo OK: Docker Full Stack services stopped

echo [4/5] Cleaning up Docker resources...
docker system prune -f >nul 2>&1
echo OK: Docker cleanup completed

echo [5/5] All services stopped and cleaned up!
goto end

:end
echo.
echo ========================================
echo    Services Stopped
echo ========================================
echo.
echo All requested services have been stopped.
echo.
echo To start services again, run: start.bat
echo.
echo Press any key to close this window...
pause >nul