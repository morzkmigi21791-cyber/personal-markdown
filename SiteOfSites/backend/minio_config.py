"""
Конфигурация MinIO для Site of Sites
Скопируйте этот файл в .env и настройте под ваши нужды
"""

# MinIO Configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "Qwerty"
MINIO_SECRET_KEY = "19216811!"
MINIO_SECURE = False
MINIO_BUCKET_NAME = "mybucket"

# Database Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "Sctorlorn25565"
DB_NAME = "siteofsites"

# JWT Configuration
SECRET_KEY = "@37!34Hif77+UIfgE22&&1#eee2EC1#$"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS Configuration
ALLOWED_ORIGINS = "http://localhost:3000"

