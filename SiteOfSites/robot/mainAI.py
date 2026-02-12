from gigachat import GigaChat
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Optional

# Настройка API ключа (В продакшене лучше использовать переменные окружения)
# Получите ключ на https://developers.sber.ru/ (Client Secret / Authorization Key)
# Это длинная строка Base64
GIGACHAT_CREDENTIALS = "MDE5YzQ3MzAtM2EwYS03MWJiLWE0NzctNGE1NmU3ZDg5MTE0Ojc3OWRkNmJmLTkyZmItNDZkNC1hNTQ4LTAzYzU2YzEyZTY5Mw=="

# Инициализация модели
# Клиент GigaChat будет создаваться в контексте запроса

app = FastAPI(title="SiteOfSites AI Support")

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

def load_knowledge_base():
    """Загружает базу знаний из JSON файла. Читает файл каждый раз, чтобы подхватывать обновления."""
    kb_path = "knowledge_base.json"
    if not os.path.exists(kb_path):
        return "{}"
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка чтения базы знаний: {e}")
        return "{}"

@app.post("/api/ai/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Загружаем актуальную базу знаний
        knowledge_context = load_knowledge_base()

        # 2. Формируем системный промпт
        system_instruction = f"""
        Ты — интеллектуальный помощник службы поддержки проекта "SiteOfSites".
        
        Твои задачи:
        1. Помогать пользователям с вопросами по хостингу сайтов, загрузке файлов и настройке проектов.
        2. Быть вежливым, кратким и профессиональным.
        
        Твои ограничения (РАМКИ):
        1. НЕ отвечай на вопросы, не связанные с веб-разработкой, хостингом или IT (например, не говори о политике, кулинарии или религии). Если спросят — вежливо откажись и вернись к теме сервиса.
        2. НЕ раскрывай внутреннюю архитектуру системы (какая БД, какой язык бэкенда и т.д.), говори только о пользовательском функционале.
        3. Используй предоставленную ниже БАЗУ ЗНАНИЙ для ответов на фактические вопросы.
        4. Если ответа нет в базе знаний, используй свои общие знания о веб-хостинге, но предупреди, что это общая информация.
        
        БАЗА ЗНАНИЙ (JSON):
        {knowledge_context}
        """

        # 3. Отправляем запрос в GigaChat
        # verify_ssl_certs=False отключает проверку сертификатов (полезно для РФ сертификатов на Windows)
        with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
            response = giga.chat({
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": request.message}
                ]
            })
            
            # Извлекаем текст ответа
            reply_text = response.choices[0].message.content
        
        return {
            "reply": reply_text,
            "status": "success"
        }

    except Exception as e:
        print(f"ОШИБКА ГЕНЕРАЦИИ: {e}") # Вывод ошибки в консоль сервера
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "AI Support Service is running"}

if __name__ == "__main__":
    import uvicorn
    # Запускаем на порту 8001, чтобы не конфликтовать с основным main.py (который обычно на 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)