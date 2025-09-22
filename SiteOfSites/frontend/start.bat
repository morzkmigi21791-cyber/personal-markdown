@echo off
chcp 65001 >nul
echo ========================================
echo    Site of Sites - Frontend Server
echo ========================================
echo.

echo Проверка зависимостей...
if not exist "node_modules" (
    echo ⚠️  Зависимости не найдены. Устанавливаю...
    npm install
    echo ✅ Зависимости установлены
) else (
    echo ✅ Зависимости найдены
)

echo.
echo 🚀 Запуск React development сервера...
echo Frontend: http://localhost:3000
echo.
npm start
