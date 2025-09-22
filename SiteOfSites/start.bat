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

echo [5/5] Checking MinIO...
docker --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker not found. MinIO will be unavailable
    echo    Install Docker Desktop from https://docker.com
) else (
    echo OK: Docker found
)

echo.
echo Starting servers...
echo.

echo [1/3] Starting MinIO...
docker ps --filter "name=minio" --format "{{.Names}}" | findstr "minio" >nul
if errorlevel 1 (
    echo Starting MinIO...
    docker run -d --name minio -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=Qwerty" -e "MINIO_ROOT_PASSWORD=19216811!" -v minio_data:/data quay.io/minio/minio server /data --console-address ":9001" >nul 2>&1
    if errorlevel 1 (
        echo WARNING: MinIO failed to start, continuing without it
    ) else (
        echo OK: MinIO started
        timeout /t 5 /nobreak >nul
    )
) else (
    echo OK: MinIO already running
)

echo [2/3] Starting Backend server...
start "Site of Sites - Backend" cmd /k "cd backend && call venv\Scripts\activate && python run.py"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend server...
start "Site of Sites - Frontend" cmd /k "cd frontend && npm start"

echo.
echo OK: All services are starting...
echo.
echo Service Information:
echo    Backend API:  http://localhost:8000
echo    Frontend:     http://localhost:3000
echo    API Docs:     http://localhost:8000/docs
echo    MinIO API:    http://localhost:9000
echo    MinIO Console: http://localhost:9001
echo.
echo MinIO Access:
echo    Login: Qwerty
echo    Password: 19216811!
echo.
echo Management:
echo    - To stop servers, close the command windows
echo    - To manage MinIO use start_minio.bat / stop_minio.bat
echo    - Server logs are displayed in separate windows
echo.
echo Press any key to close this window...
pause >nul
