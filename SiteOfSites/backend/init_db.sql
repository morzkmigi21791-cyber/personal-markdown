-- Инициализация базы данных для Site of Sites
-- Этот файл выполняется при первом запуске PostgreSQL контейнера

-- Создаем базу данных (если не существует)
-- CREATE DATABASE siteofsites;

-- Подключаемся к базе данных
\c siteofsites;

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создаем таблицы (они будут созданы автоматически через SQLAlchemy)
-- Но можно добавить дополнительные индексы для производительности

-- Создаем индексы для оптимизации запросов
-- (будут созданы после создания таблиц через миграции)

-- Настройки для производительности
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Перезагружаем конфигурацию
SELECT pg_reload_conf();
