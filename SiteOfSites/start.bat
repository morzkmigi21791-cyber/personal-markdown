@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Quick Start
echo ========================================
echo.

echo Checking dependencies...
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install Python 3.8+ from https://python.org
    pause
    exit /b 1
) else (
    echo OK: Python found
)

echo [2/4] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Install Node.js from https://nodejs.org
    pause
    exit /b 1
) else (
    echo OK: Node.js found
)

echo [3/4] Checking Backend dependencies...
if not exist "backend\venv" (
    echo WARNING: Virtual environment not found. Creating...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
    echo OK: Virtual environment created
) else (
    echo OK: Virtual environment found
)

echo [4/5] Checking Frontend dependencies...
if not exist "frontend\node_modules" (
    echo WARNING: Frontend dependencies not found. Installing...
    cd frontend
    npm install
    cd ..
    echo OK: Frontend dependencies installed
) else (
    echo OK: Frontend dependencies found
)

echo [5/6] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found! Install Docker Desktop from https://docker.com
    pause
    exit /b 1
) else (
    echo OK: Docker found
)

echo [6/6] Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker Compose not found. Using docker compose instead...
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    echo OK: Docker Compose found
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo.
echo Starting servers...
echo.

echo [1/4] Starting Docker services (MinIO + Nginx)...
%DOCKER_COMPOSE_CMD% down >nul 2>&1
%DOCKER_COMPOSE_CMD% up -d
if errorlevel 1 (
    echo WARNING: Docker services failed to start, continuing without them
) else (
    echo OK: Docker services started
    timeout /t 5 /nobreak >nul
)

echo [2/4] Running database migration...
cd backend
call venv\Scripts\activate
python migrate_hosting.py
if errorlevel 1 (
    echo WARNING: Database migration failed, continuing anyway
) else (
    echo OK: Database migration completed
)

echo [2.5/4] Fixing enum values...
python fix_enum_migration.py
if errorlevel 1 (
    echo WARNING: Enum fix failed, continuing anyway
) else (
    echo OK: Enum values fixed
)
cd ..

echo [3/4] Starting Backend server...
start "Site of Sites - Backend" cmd /k "cd backend && call venv\Scripts\activate && python run.py"

timeout /t 3 /nobreak >nul

echo [4/4] Starting Frontend server...
start "Site of Sites - Frontend" cmd /k "cd frontend && npm start"

timeout /t 3 /nobreak >nul

echo [5/5] All services started successfully!
echo.
echo ========================================
echo    Service Information
echo ========================================
echo.
echo Main Services:
echo    Frontend:     http://localhost:3000
echo    Backend API:  http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo.
echo Docker Services:
echo    Nginx:        http://localhost (port 80)
echo    MinIO API:    http://localhost:9000
echo    MinIO Console: http://localhost:9001
echo.
echo Site Hosting:
echo    Main Site:    http://localhost
echo    Subdomains:   http://SUBDOMAIN.localhost
echo    Example:      http://mysite.localhost
echo.
echo MinIO Access:
echo    Login: Qwerty
echo    Password: 19216811!
echo.
echo Management:
echo    - To stop all services: run stop.bat
echo    - To stop Docker only: docker-compose down
echo    - Server logs are displayed in separate windows
echo.
echo ========================================
echo.
echo Press any key to close this window...
pause >nul
