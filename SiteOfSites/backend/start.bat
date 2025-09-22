@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Backend Server
echo ========================================
echo.

echo Проверка виртуального окружения...
if not exist "venv" (
    echo ⚠️  Виртуальное окружение не найдено. Создаю...
    python -m venv venv
    call venv\Scripts\activate
    echo Установка зависимостей...
    pip install -r requirements.txt
    echo ✅ Виртуальное окружение создано и зависимости установлены
) else (
    echo ✅ Виртуальное окружение найдено
    call venv\Scripts\activate
)

echo.
echo Проверка MinIO подключения...
python -c "from s3 import minio_client; print('✅ MinIO подключен' if minio_client else '❌ MinIO недоступен')" 2>nul
if errorlevel 1 (
    echo ❌ Ошибка подключения к MinIO
    echo Убедитесь, что MinIO запущен на localhost:9000
    pause
    exit /b 1
)

echo.
echo 🚀 Запуск FastAPI сервера...
echo Backend API: http://localhost:8000
echo API Docs:    http://localhost:8000/docs
echo.
python run.py
