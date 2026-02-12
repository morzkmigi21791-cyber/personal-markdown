@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Universal Start
echo ========================================
echo.

echo Choose startup mode:
echo [1] Docker (Recommended - Full Stack)
echo [2] Development (Local Python + Node.js)
echo [3] Infrastructure Only (Docker MinIO + Nginx)
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto docker_full
if "%choice%"=="2" goto development
if "%choice%"=="3" goto infrastructure
echo Invalid choice. Exiting...
pause
exit /b 1

:docker_full
echo.
echo Starting Site of Sites with Docker (Full Stack)...
echo.

echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found! Install Docker Desktop from https://docker.com
    pause
    exit /b 1
) else (
    echo OK: Docker found
)

echo Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker Compose not found. Using docker compose instead...
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    echo OK: Docker Compose found
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo [1/3] Stopping existing containers...
%DOCKER_COMPOSE_CMD% -f docker-compose.full.yml down >nul 2>&1

echo [2/3] Building and starting services...
%DOCKER_COMPOSE_CMD% -f docker-compose.full.yml up --build -d

if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

echo [3/3] Running database migrations...
docker exec siteofsites_backend python init_db.py

echo.
echo ========================================
echo    Docker Services Started
echo ========================================
echo.
echo Main Site:    http://localhost
echo Frontend:     http://localhost:3000
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo MinIO Console: http://localhost:9001
echo.
echo MinIO Login: Qwerty / 19216811!
echo.
echo To stop: run stop.bat
echo.
goto end

:development
echo.
echo Starting Site of Sites in Development Mode...
echo.

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install Python 3.8+ from https://python.org
    pause
    exit /b 1
) else (
    echo OK: Python found
)

echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Install Node.js from https://nodejs.org
    pause
    exit /b 1
) else (
    echo OK: Node.js found
)

echo [3/5] Checking Backend dependencies...
if not exist "backend\venv" (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
    pip install httpx
    cd ..
    echo OK: Virtual environment created
) else (
    echo OK: Virtual environment found
)

echo [4/5] Checking Frontend dependencies...
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
    echo OK: Frontend dependencies installed
) else (
    echo OK: Frontend dependencies found
)

echo [5/5] Starting Docker infrastructure...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

%DOCKER_COMPOSE_CMD% down >nul 2>&1
%DOCKER_COMPOSE_CMD% up -d
if errorlevel 1 (
    echo WARNING: Docker services failed to start, continuing without them
) else (
    echo OK: Docker services started
    timeout /t 5 /nobreak >nul
)

echo Running database migration...
cd backend
call venv\Scripts\activate
echo Installing missing dependencies (httpx)...
pip install httpx >nul 2>&1
python migrate_hosting.py 2>nul
python fix_enum_migration.py 2>nul
cd ..

echo Starting Backend server...
start "Site of Sites - Backend" cmd /k "cd backend && call venv\Scripts\activate && python run.py"

echo Starting AI Bot server...
start "Site of Sites - AI Bot" cmd /k "cd robot && call run_bot.bat"

timeout /t 3 /nobreak >nul

echo Starting Frontend server...
start "Site of Sites - Frontend" cmd /k "cd frontend && set DANGEROUSLY_DISABLE_HOST_CHECK=true && npm start"

echo.
echo ========================================
echo    Development Services Started
echo ========================================
echo.
echo Frontend:     http://localhost:3000
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Main Site:    http://localhost
echo MinIO Console: http://localhost:9001
echo.
echo MinIO Login: Qwerty / 19216811!
echo.
echo To stop: run stop.bat
echo.
goto end

:infrastructure
echo.
echo Starting Infrastructure Only (MinIO + Nginx)...
echo.

echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found! Install Docker Desktop from https://docker.com
    pause
    exit /b 1
) else (
    echo OK: Docker found
)

echo Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo Starting infrastructure services...
%DOCKER_COMPOSE_CMD% down >nul 2>&1
%DOCKER_COMPOSE_CMD% up -d

if errorlevel 1 (
    echo ERROR: Failed to start infrastructure services
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Infrastructure Services Started
echo ========================================
echo.
echo Nginx:        http://localhost (port 80)
echo MinIO API:    http://localhost:9000
echo MinIO Console: http://localhost:9001
echo.
echo MinIO Login: Qwerty / 19216811!
echo.
echo To stop: run stop.bat
echo.
goto end

:end
echo Press any key to close this window...
pause >nul
