import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Загружаем переменные окружения
load_dotenv()

# Настройки базы данных PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "siteofsites")

# URL для подключения к PostgreSQL
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# JWT настройки
SECRET_KEY = os.getenv("SECRET_KEY", "@37!34Hif77+UIfgE22&&1#eee2EC1#$")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS настройки
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
