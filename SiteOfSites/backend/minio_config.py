"""
Конфигурация MinIO для Site of Sites
Скопируйте этот файл в .env и настройте под ваши нужды
"""
import os

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "Qwerty")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "19216811!")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "mybucket")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Sctorlorn25565")
DB_NAME = os.getenv("DB_NAME", "siteofsites")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "@37!34Hif77+UIfgE22&&1#eee2EC1#$")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
