@echo off
chcp 65001 >nul
echo ========================================
echo    MinIO Stop
echo ========================================
echo.

echo Stopping MinIO...
docker stop minio >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: MinIO stopped
) else (
    echo WARNING: MinIO was not running
)

echo.
echo Removing container...
docker rm minio >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Container removed
) else (
    echo WARNING: Container not found
)

echo.
echo Data saved in Docker volume 'minio_data'
echo    Files will be restored on next startup
echo.
pause
