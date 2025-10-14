@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Log Viewer
echo ========================================
echo.

echo Choose logs to view:
echo [1] Backend logs (real-time)
echo [2] All services logs (real-time)
echo [3] Backend logs (last 50 lines)
echo [4] All services logs (last 50 lines)
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto backend_realtime
if "%choice%"=="2" goto all_realtime
if "%choice%"=="3" goto backend_last50
if "%choice%"=="4" goto all_last50
echo Invalid choice. Exiting...
pause
exit /b 1

:backend_realtime
echo.
echo Viewing Backend logs (real-time)...
echo Press Ctrl+C to stop
docker logs -f siteofsites_backend
goto end

:all_realtime
echo.
echo Viewing all services logs (real-time)...
echo Press Ctrl+C to stop
docker-compose -f docker-compose.full.yml logs -f
goto end

:backend_last50
echo.
echo Backend logs (last 50 lines):
docker logs siteofsites_backend --tail 50
pause
goto end

:all_last50
echo.
echo All services logs (last 50 lines):
docker-compose -f docker-compose.full.yml logs --tail 50
pause
goto end

:end
echo.
echo Press any key to close this window...
pause >nul
