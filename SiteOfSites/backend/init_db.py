#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных PostgreSQL
"""

from database import engine, Base
from models import User

def init_db():
    print("Создание таблиц в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно!")

if __name__ == "__main__":
    init_db()
