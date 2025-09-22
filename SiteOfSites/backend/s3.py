from minio import Minio
from minio.error import S3Error
import logging
from config import (
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, 
    MINIO_SECURE, MINIO_BUCKET_NAME
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_minio_client():
    """Создает и возвращает клиент MinIO с обработкой ошибок"""
    try:
        client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        return client
    except Exception as e:
        logger.error(f"Ошибка создания MinIO клиента: {e}")
        raise

def ensure_bucket_exists(client, bucket_name):
    """Проверяет существование bucket и создает его при необходимости"""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' создан успешно")
        else:
            logger.info(f"Bucket '{bucket_name}' уже существует")
    except S3Error as e:
        logger.error(f"Ошибка при работе с bucket '{bucket_name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при работе с bucket: {e}")
        raise

# Инициализация MinIO клиента
try:
    minio_client = create_minio_client()
    ensure_bucket_exists(minio_client, MINIO_BUCKET_NAME)
    logger.info("MinIO клиент инициализирован успешно")
except Exception as e:
    logger.error(f"Критическая ошибка инициализации MinIO: {e}")
    minio_client = None

BUCKET_NAME = MINIO_BUCKET_NAME
