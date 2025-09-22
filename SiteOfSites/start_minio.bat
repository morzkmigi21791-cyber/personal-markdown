@echo off
chcp 65001 >nul
echo ========================================
echo    MinIO Auto Start
echo ========================================
echo.

echo Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker not found! Install Docker Desktop from https://docker.com
    echo.
    pause
    exit /b 1
)
echo OK: Docker found

echo.
echo Checking if MinIO is already running...
docker ps --filter "name=minio" --format "{{.Names}}" | findstr "minio" >nul
if %errorlevel% equ 0 (
    echo OK: MinIO already running!
    echo.
    echo Web Console: http://localhost:9001
    echo Login: Qwerty
    echo Password: 19216811!
    echo.
    pause
    exit /b 0
)

echo.
echo Stopping old container (if exists)...
docker stop minio >nul 2>&1
docker rm minio >nul 2>&1

echo.
echo Starting MinIO...
docker run -d --name minio -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=Qwerty" -e "MINIO_ROOT_PASSWORD=19216811!" -v minio_data:/data quay.io/minio/minio server /data --console-address ":9001"

if %errorlevel% neq 0 (
    echo ERROR: Failed to start MinIO!
    echo Possible causes:
    echo - Docker not running
    echo - Ports 9000 or 9001 are busy
    echo - Network issues
    echo.
    pause
    exit /b 1
)

echo.
echo Waiting for MinIO to start (10 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo Checking status...
docker ps --filter "name=minio" --format "{{.Names}}" | findstr "minio" >nul
if %errorlevel% equ 0 (
    echo OK: MinIO started successfully!
    echo.
    echo Web Console: http://localhost:9001
    echo Login: Qwerty
    echo Password: 19216811!
    echo.
    echo Files will be saved in bucket: siteofsites-files
    echo.
    echo You can now start your application!
) else (
    echo ERROR: MinIO failed to start. Check logs:
    echo docker logs minio
)

echo.
pause