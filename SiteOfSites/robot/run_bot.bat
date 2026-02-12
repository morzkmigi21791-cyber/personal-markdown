@echo off
title SiteOfSites AI Support Bot
python requirements.py
echo Запуск интеллектуальной системы поддержки...
echo Сервер будет доступен по адресу: http://127.0.0.1:8001
echo Нажмите Ctrl+C для остановки.
python mainAI.py
pause