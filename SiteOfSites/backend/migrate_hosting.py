#!/usr/bin/env python3
"""
Миграция базы данных для добавления полей хостинга сайтов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine
from models import Base

def migrate_database():
    """Выполняет миграцию базы данных"""
    print("Начинаем миграцию базы данных...")
    
    try:
        with engine.connect() as conn:
            # Проверяем, существуют ли уже новые колонки
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'projects' 
                AND column_name IN ('subdomain', 'visibility', 'is_active', 'custom_domain', 'index_file')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            print(f"Найдены существующие колонки: {existing_columns}")
            
            # Добавляем колонки, если их нет
            if 'subdomain' not in existing_columns:
                print("Добавляем колонку subdomain...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN subdomain VARCHAR(50)"))
                conn.execute(text("CREATE INDEX ix_projects_subdomain ON projects (subdomain)"))
                conn.execute(text("ALTER TABLE projects ADD CONSTRAINT uq_projects_subdomain UNIQUE (subdomain)"))
            
            if 'visibility' not in existing_columns:
                print("Добавляем колонку visibility...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN visibility VARCHAR(20) DEFAULT 'PRIVATE'"))
            
            if 'is_active' not in existing_columns:
                print("Добавляем колонку is_active...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN is_active BOOLEAN DEFAULT FALSE"))
            
            if 'custom_domain' not in existing_columns:
                print("Добавляем колонку custom_domain...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN custom_domain VARCHAR(100)"))
            
            if 'index_file' not in existing_columns:
                print("Добавляем колонку index_file...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN index_file VARCHAR(100) DEFAULT 'index.html'"))
            
            conn.commit()
            print("Миграция успешно завершена!")
            
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("База данных успешно обновлена!")
    else:
        print("Ошибка при обновлении базы данных!")
        sys.exit(1)
