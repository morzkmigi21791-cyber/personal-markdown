FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.py .
RUN python requirements.py

# Копирование кода и базы знаний
COPY mainAI.py .
COPY knowledge_base.json .

EXPOSE 8001

CMD ["python", "mainAI.py"]