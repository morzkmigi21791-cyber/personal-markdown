import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Загружаем переменные окружения
load_dotenv()

# Настройки базы данных PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Sctorlorn25565")
DB_NAME = os.getenv("DB_NAME", "siteofsites")

# URL для подключения к PostgreSQL
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# JWT настройки
SECRET_KEY = os.getenv("SECRET_KEY", "@37!34Hif77+UIfgE22&&1#eee2EC1#$")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS настройки
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# MinIO настройки
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "Qwerty")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "19216811!")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "mybucket")

# Разрешенные форматы файлов
ALLOWED_FILE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.css', '.html', '.js'}
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/webp', 
    'text/css', 'text/html', 'application/javascript'
}

# Максимальный размер файла (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024
