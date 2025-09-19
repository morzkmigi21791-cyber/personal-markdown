#!/usr/bin/env python3
"""
Скрипт для миграции базы данных
Добавляет новые поля в таблицу users и создает таблицу projects
"""

from sqlalchemy import create_engine, text
from database import Base, engine, SessionLocal
from models import User, Project
import string
import random

def generate_unique_id(db):
    """Генерирует уникальный ID длиной от 5 до 10 символов (только буквы и цифры)"""
    while True:
        length = random.randint(5, 10)
        unique_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
        # Проверяем, что такой ID не существует
        if not db.query(User).filter(User.unique_id == unique_id).first():
            return unique_id

def migrate_database():
    """Выполняет миграцию базы данных"""
    print("Начинаем миграцию базы данных...")
    
    # Создаем все таблицы (включая новые)
    Base.metadata.create_all(bind=engine)
    print("✓ Таблицы созданы/обновлены")
    
    # Проверяем, нужно ли добавить unique_id для существующих пользователей
    db = SessionLocal()
    try:
        users_without_unique_id = db.query(User).filter(User.unique_id.is_(None)).all()
        
        if users_without_unique_id:
            print(f"Найдено {len(users_without_unique_id)} пользователей без unique_id")
            
            for user in users_without_unique_id:
                user.unique_id = generate_unique_id(db)
                print(f"✓ Добавлен unique_id для пользователя {user.nickname}: {user.unique_id}")
            
            db.commit()
            print("✓ Все unique_id добавлены")
        else:
            print("✓ Все пользователи уже имеют unique_id")
            
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Миграция завершена успешно!")

if __name__ == "__main__":
    migrate_database()

