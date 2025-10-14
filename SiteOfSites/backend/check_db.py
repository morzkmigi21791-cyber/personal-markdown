#!/usr/bin/env python3
"""
Проверка состояния базы данных и исправление проблем
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Настройки базы данных
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Sctorlorn25565")
DB_NAME = os.getenv("DB_NAME", "siteofsites")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_database():
    """Проверка состояния базы данных"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Проверяем подключение
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL подключен: {version}")
            
            # Проверяем существование таблиц
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Найдены таблицы: {', '.join(tables)}")
                
                # Проверяем таблицу users
                if 'users' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM users;"))
                    user_count = result.fetchone()[0]
                    print(f"✅ Пользователей в базе: {user_count}")
                else:
                    print("❌ Таблица 'users' не найдена")
                    
                # Проверяем таблицу projects
                if 'projects' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM projects;"))
                    project_count = result.fetchone()[0]
                    print(f"✅ Проектов в базе: {project_count}")
                else:
                    print("❌ Таблица 'projects' не найдена")
            else:
                print("❌ Таблицы не найдены - нужно запустить миграции")
                
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False
    
    return True

def create_tables():
    """Создание таблиц если их нет"""
    try:
        from models import Base
        engine = create_engine(DATABASE_URL)
        
        print("🔄 Создание таблиц...")
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы успешно")
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Проверка базы данных...")
    
    if not check_database():
        print("🔄 Попытка создания таблиц...")
        if create_tables():
            print("✅ База данных исправлена")
        else:
            print("❌ Не удалось исправить базу данных")
            sys.exit(1)
    else:
        print("✅ База данных в порядке")
