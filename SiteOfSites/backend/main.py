from fastapi import FastAPI, HTTPException, Depends, Response, status, Request, UploadFile, File, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta, datetime
from typing import List, Optional
import re
import string
import random
import logging
import hashlib
import httpx

from starlette.responses import StreamingResponse

try:
    import geoip2.database
except ImportError:
    geoip2 = None
    print("Warning: geoip2 module not found. Country detection will be disabled.")

from s3 import minio_client, BUCKET_NAME
import io
import os
from config import ALLOWED_FILE_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_FILE_SIZE, DOMAIN, SITE_PROTOCOL, ACCESS_TOKEN_EXPIRE_MINUTES


from database import SessionLocal, engine
from models import Base, User, Project, ProjectVisit, ChatHistory
from schemas import (
    UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    ProjectCreate, ProjectUpdate, ProjectResponse,
    UserWithProjects, UserSearchResult, Token, SiteHostingConfig,
    ProjectStats, ProjectStatsSummary, ChatMessageCreate, ChatMessageResponse
)
from security import hash_password, verify_password, create_access_token, verify_token
from config import ALLOWED_ORIGINS

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Site of Sites API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка OAuth2 для Swagger UI (и извлечения токена из заголовка)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# URL AI сервиса (из переменной окружения или дефолт)
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency для получения текущего пользователя
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    # Проверяем токен в заголовке (Bearer), если нет - в куках
    if not token:
        token = access_token
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не предоставлен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(token)
        email: str = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Dependency для получения текущего пользователя (опционально)
async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    if not token:
        token = access_token
    
    if not token:
        return None

    try:
        payload = verify_token(token)
        email: str = payload.get("sub")
    except Exception:
        return None
    
    user = db.query(User).filter(User.email == email).first()
    return user

# Валидация email
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Генерация уникального ID
def generate_unique_id(db: Session) -> str:
    """Генерирует уникальный ID длиной от 5 до 10 символов (только буквы и цифры)"""
    while True:
        length = random.randint(5, 10)
        unique_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
        # Проверяем, что такой ID не существует
        if not db.query(User).filter(User.unique_id == unique_id).first():
            return unique_id

# Валидация файлов
def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Валидирует загружаемый файл по расширению, MIME-типу и размеру"""
    if not file.filename:
        return False, "Имя файла не может быть пустым"
    
    # Проверяем расширение файла
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in ALLOWED_FILE_EXTENSIONS:
        return False, f"Недопустимое расширение файла. Разрешены: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
    
    # Проверяем MIME-тип (более мягкая проверка)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # MIME-тип не соответствует ожидаемому, но не блокируем загрузку
        pass
    
    return True, "Файл валиден"

def validate_file_size(file_data: bytes) -> tuple[bool, str]:
    """Проверяет размер файла"""
    if len(file_data) > MAX_FILE_SIZE:
        return False, f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024*1024)}MB"
    return True, "Размер файла допустим"

def create_project_images_folder(user_unique_id: str, project_id: int):
    """Создает папку images для проекта в MinIO"""
    if not minio_client:
        return False
    
    try:
        # Создаем пустой файл-маркер для папки images
        folder_marker = f"{user_unique_id}/{project_id}/images/.gitkeep"
        minio_client.put_object(
            BUCKET_NAME,
            folder_marker,
            io.BytesIO(b""),
            length=0,
            content_type="text/plain"
        )
        return True
    except Exception as e:
        print(f"Ошибка создания папки images: {e}")
        return False

def validate_subdomain_unique(subdomain: str, db: Session, project_id: int = None) -> tuple[bool, str]:
    """Проверяет уникальность поддомена"""
    if not subdomain:
        return True, "Поддомен не указан"
    
    # Проверяем, что поддомен не занят другим проектом
    query = db.query(Project).filter(Project.subdomain == subdomain)
    if project_id:
        query = query.filter(Project.id != project_id)
    
    existing_project = query.first()
    if existing_project:
        return False, f"Поддомен '{subdomain}' уже занят"
    
    return True, "Поддомен доступен"

def get_site_files_from_minio(user_unique_id: str, project_id: int):
    """Получает файлы сайта из MinIO"""
    if not minio_client:
        return []
    
    try:
        # Получаем файлы из корневой папки проекта (не images)
        objects = minio_client.list_objects(
            BUCKET_NAME,
            prefix=f"{user_unique_id}/{project_id}/",
            recursive=True
        )
        
        site_files = []
        for obj in objects:
            # Пропускаем только служебные файлы
            if not obj.object_name.endswith('.gitkeep'):
                prefix = f"{user_unique_id}/{project_id}/"
                relative_path = obj.object_name[len(prefix):] if obj.object_name.startswith(prefix) else obj.object_name
                site_files.append({
                    "filename": relative_path,
                    "size": obj.size,
                    "last_modified": obj.last_modified
                })
        
        return site_files
    except Exception as e:
        print(f"Ошибка получения файлов сайта: {e}")
        return []

def serve_site_file(user_unique_id: str, project_id: int, filename: str):
    """Отдает файл сайта из MinIO"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    try:
        # Формируем путь к файлу
        full_filename = f"{user_unique_id}/{project_id}/{filename}"
        
        # Получаем файл из MinIO
        response = minio_client.get_object(BUCKET_NAME, full_filename)
        
        # Определяем MIME-тип по расширению
        file_extension = os.path.splitext(filename)[1].lower()
        mime_type_map = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.json': 'application/json',
            '.txt': 'text/plain'
        }
        media_type = mime_type_map.get(file_extension, 'application/octet-stream')
        
        # Создаем генератор для стриминга с правильным закрытием соединения
        def iterfile():
            try:
                for chunk in response.stream(1024 * 1024):  # Читаем по 1MB
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        # Получаем ETag из заголовков MinIO. Не генерируем случайный, чтобы избежать циклов обновления.
        etag = response.headers.get("ETag")
        
        headers = {
            "Cache-Control": "no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Last-Modified": response.headers.get("Last-Modified", ""),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN"
        }
        if etag:
            headers["ETag"] = etag

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers=headers
        )
        
    except Exception as e:
        logging.error(f"Ошибка отдачи файла {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ошибка отдачи файла: {str(e)}"
        )

# Вспомогательная функция для записи статистики
def record_project_visit(project: Project, request: Request, db: Session):
    """Записывает визит, если проект публичный или доступен по ссылке"""
    # Если проект приватный - статистику не пишем (заморожена)
    if project.visibility == "PRIVATE":
        return

    try:
        # Определение источника перехода
        referer = request.headers.get("referer", "")
        source_type = "direct"
        
        # Проверяем, пришел ли пользователь со страницы профиля нашего сайта
        # Предполагаем, что DOMAIN содержится в config.py
        if DOMAIN in referer and "/profile/" in referer:
            source_type = "profile"
        elif referer:
            source_type = "external"
            
        # Определение страны
        country = "Неизвестно"
        
        # Получаем IP адрес клиента
        client_ip = "127.0.0.1"
        if request.client:
            client_ip = request.client.host
            
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
            
        # ЛОГИРОВАНИЕ: Проверяем, какой IP видит сервер
        logging.info(f"DEBUG STATS: Client IP={client_ip}, X-Forwarded-For={request.headers.get('x-forwarded-for')}")

        # Защита от накрутки (фарма посещений)
        user_agent = request.headers.get("user-agent", "")
        # Создаем уникальный хеш посетителя на основе IP и User-Agent
        visitor_hash = hashlib.sha256(f"{client_ip}{user_agent}".encode()).hexdigest()
        
        # Проверяем, был ли этот посетитель на этом проекте за последние 24 часа
        recent_visit = db.query(ProjectVisit).filter(
            ProjectVisit.project_id == project.id,
            ProjectVisit.visitor_hash == visitor_hash,
            ProjectVisit.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).first()
        
        if recent_visit:
            return # Не засчитываем повторное посещение
            
        # Используем GeoIP2 для определения страны
        geoip_db_path = "GeoLite2-Country.mmdb"
        if geoip2 and os.path.exists(geoip_db_path):
            try:
                with geoip2.database.Reader(geoip_db_path) as reader:
                    response = reader.country(client_ip)
                    if response.country.iso_code:
                        country = response.country.iso_code
            except Exception as e:
                logging.error(f"GeoIP lookup error for {client_ip}: {e}")
                pass
        else:
            if not geoip2:
                logging.warning("GeoIP WARNING: Библиотека geoip2 не установлена или не импортирована.")
            if not os.path.exists(geoip_db_path):
                logging.warning(f"GeoIP WARNING: Файл базы данных не найден по пути: {os.path.abspath(geoip_db_path)}")
        
        # Fallback на Cloudflare
        if country == "Неизвестно":
            country = request.headers.get("CF-IPCountry", "Неизвестно")
        
        # Создаем запись
        visit = ProjectVisit(
            project_id=project.id,
            country_code=country,
            source_type=source_type,
            visitor_hash=visitor_hash
        )
        db.add(visit)
        db.commit()
    except Exception as e:
        # Ошибки статистики не должны ломать отдачу сайта
        logging.error(f"Ошибка записи статистики: {e}")
        # В случае ошибки отката нет, так как мы в отдельной транзакции или 
        # просто игнорируем, чтобы не блокировать основной поток, 
        # но здесь db сессия общая, поэтому лучше сделать rollback при ошибке
        db.rollback()

@app.get("/")
async def root():
    return {"message": "Site of Sites API"}

@app.get("/api/config")
async def get_config():
    """Возвращает публичную конфигурацию сервера"""
    return {
        "domain": DOMAIN,
        "protocol": SITE_PROTOCOL
    }

@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    from models import User
    
    # Проверяем, существует ли пользователь с таким email
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
    
    # Проверяем, существует ли пользователь с таким никнеймом
    db_user_nickname = db.query(User).filter(User.nickname == user.nickname).first()
    if db_user_nickname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким никнеймом уже существует"
        )
    
    # Создаем нового пользователя
    hashed_password = hash_password(user.password)
    unique_id = generate_unique_id(db)
    db_user = User(
        email=user.email,
        nickname=user.nickname,
        password_hash=hashed_password,
        unique_id=unique_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    from models import User
    
    # Находим пользователя по email
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    # Устанавливаем HTTP-only куки
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Успешный выход из системы"}

# Поиск пользователей
@app.get("/api/users/search", response_model=List[UserSearchResult])
async def search_users(q: str, db: Session = Depends(get_db)):
    """Поиск пользователей по имени или уникальному ID"""
    if len(q) < 2:
        return []
    
    # Поиск по никнейму или уникальному ID
    users = db.query(User).filter(
        (User.nickname.ilike(f"%{q}%")) | (User.unique_id.ilike(f"%{q}%"))
    ).limit(5).all()
    
    return users

# Получение профиля пользователя
@app.get("/api/users/{user_id}", response_model=UserWithProjects)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Получение профиля пользователя по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

# Получение профиля пользователя по уникальному ID
@app.get("/api/users/by-unique-id/{unique_id}", response_model=UserWithProjects)
async def get_user_profile_by_unique_id(unique_id: str, db: Session = Depends(get_db)):
    """Получение профиля пользователя по уникальному ID"""
    user = db.query(User).filter(User.unique_id == unique_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

# Обновление профиля
@app.put("/api/users/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля текущего пользователя"""
    
    # Проверяем, что никнейм не занят другим пользователем
    if profile_data.nickname and profile_data.nickname != current_user.nickname:
        existing_user = db.query(User).filter(
            User.nickname == profile_data.nickname,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким никнеймом уже существует"
            )
    
    # Обновляем поля
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname
    if profile_data.description is not None:
        current_user.description = profile_data.description
    if profile_data.avatar is not None:
        current_user.avatar = profile_data.avatar
    if profile_data.profile_cover is not None:
        current_user.profile_cover = profile_data.profile_cover
    if profile_data.page_background is not None:
        current_user.page_background = profile_data.page_background
    if profile_data.projects_background is not None:
        current_user.projects_background = profile_data.projects_background
    if profile_data.card_color is not None:
        current_user.card_color = profile_data.card_color
    
    db.commit()
    db.refresh(current_user)
    return current_user

# Управление проектами
@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового проекта"""
    # Проверяем уникальность поддомена, если он указан
    if project.subdomain:
        is_unique, message = validate_subdomain_unique(project.subdomain, db)
        if not is_unique:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
    
    db_project = Project(
        title=project.title,
        description=project.description,
        owner_id=current_user.id,
        subdomain=project.subdomain,
        visibility=project.visibility,
        is_active=project.is_active,
        index_file=project.index_file
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Автоматически создаем папку images для проекта
    create_project_images_folder(current_user.unique_id, db_project.id)
    
    return db_project

@app.get("/api/projects", response_model=List[ProjectResponse])
async def get_user_projects(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение проектов текущего пользователя"""
    response.headers["Cache-Control"] = "no-cache"
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects

@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление проекта"""
    db_project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверяем уникальность поддомена, если он указан и изменился
    if project.subdomain and project.subdomain != db_project.subdomain:
        is_unique, message = validate_subdomain_unique(project.subdomain, db, project_id)
        if not is_unique:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
    
    # Обновляем поля только если они переданы
    if project.title is not None:
        db_project.title = project.title
    if project.description is not None:
        db_project.description = project.description
    if project.subdomain is not None:
        db_project.subdomain = project.subdomain
    if project.visibility is not None:
        db_project.visibility = project.visibility
    if project.is_active is not None:
        db_project.is_active = project.is_active
    if project.index_file is not None:
        db_project.index_file = project.index_file
    
    db.commit()
    db.refresh(db_project)
    return db_project

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление проекта"""
    db_project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    db.delete(db_project)
    db.commit()
    return {"message": "Проект удален"}


@app.post("/api/upload/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Загрузка файла с валидацией (в корень пользователя)"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    try:
        # Валидация файла
        is_valid, error_message = validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Читаем содержимое файла
        file_data = await file.read()
        
        # Проверяем размер файла
        size_valid, size_error = validate_file_size(file_data)
        if not size_valid:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=size_error
            )
        
        # Генерируем уникальное имя файла
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{current_user.unique_id}/{file.filename}"
        
        # Сохраняем в MinIO
        minio_client.put_object(
            BUCKET_NAME,
            unique_filename,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type
        )
        
        return {
            "message": f"Файл {file.filename} успешно загружен",
            "filename": unique_filename,
            "original_name": file.filename,
            "size": len(file_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки файла: {str(e)}"
        )

@app.get("/api/download/{filename}")
async def download_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Скачивание файла с проверкой прав доступа"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    try:
        # Проверяем, что файл принадлежит пользователю
        if not filename.startswith(f"{current_user.unique_id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав доступа к этому файлу"
            )
        
        # Получаем файл из MinIO
        response = minio_client.get_object(BUCKET_NAME, filename)
        
        # Определяем MIME-тип по расширению
        file_extension = os.path.splitext(filename)[1].lower()
        mime_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.css': 'text/css',
            '.html': 'text/html',
            '.js': 'application/javascript'
        }
        media_type = mime_type_map.get(file_extension, 'application/octet-stream')
        
        # Для скачивания тоже лучше использовать безопасный стриминг
        def iterfile():
            try:
                for chunk in response.stream(1024 * 1024):
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(filename)}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл не найден: {str(e)}"
        )

@app.get("/api/files/")
async def list_user_files(current_user: User = Depends(get_current_user)):
    """Получение списка файлов пользователя"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    try:
        # Получаем список объектов с префиксом пользователя
        objects = minio_client.list_objects(
            BUCKET_NAME, 
            prefix=f"{current_user.unique_id}/",
            recursive=True
        )
        
        files = []
        for obj in objects:
            files.append({
                "filename": obj.object_name,
                "original_name": os.path.basename(obj.object_name),
                "size": obj.size,
                "last_modified": obj.last_modified
            })
        
        return {"files": files}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения списка файлов: {str(e)}"
        )

@app.delete("/api/files/{filename}")
async def delete_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Удаление файла пользователя"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    try:
        # Проверяем, что файл принадлежит пользователю
        if not filename.startswith(f"{current_user.unique_id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав доступа к этому файлу"
            )
        
        # Удаляем файл из MinIO
        minio_client.remove_object(BUCKET_NAME, filename)
        
        return {"message": f"Файл {os.path.basename(filename)} успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления файла: {str(e)}"
        )

# Управление файлами проектов
@app.post("/api/projects/{project_id}/files")
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    folder: str = "root",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Загрузка файла в проект (только автор)"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    # Проверяем, что проект принадлежит пользователю
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден или нет прав доступа"
        )
    
    # Проверяем, что папка существует (только root и images)
    if folder not in ["root", "images"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимая папка. Разрешены только 'root' и 'images'"
        )
    
    try:
        # Валидация файла
        is_valid, error_message = validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Читаем содержимое файла
        file_data = await file.read()
        
        # Проверяем размер файла
        size_valid, size_error = validate_file_size(file_data)
        if not size_valid:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=size_error
            )
        
        # Генерируем путь для файла: user_id/project_id/folder/filename
        if folder == "root":
            unique_filename = f"{current_user.unique_id}/{project_id}/{file.filename}"
        else:  # images
            unique_filename = f"{current_user.unique_id}/{project_id}/{folder}/{file.filename}"
        
        # Сохраняем в MinIO
        minio_client.put_object(
            BUCKET_NAME,
            unique_filename,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Отключаем хостинг при изменении файлов, чтобы гарантировать обновление контента
        project.is_active = False
        db.commit()
        
        return {
            "message": f"Файл {file.filename} успешно загружен в папку {folder}",
            "filename": unique_filename,
            "original_name": file.filename,
            "folder": folder,
            "size": len(file_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки файла: {str(e)}"
        )

@app.get("/api/projects/{project_id}/files")
async def get_project_files(
    project_id: int,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка файлов проекта (только автор)"""
    response.headers["Cache-Control"] = "no-cache"
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    # Проверяем, что проект принадлежит пользователю
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден или нет прав доступа"
        )
    
    try:
        # Получаем список файлов проекта из MinIO
        objects = minio_client.list_objects(
            BUCKET_NAME, 
            prefix=f"{current_user.unique_id}/{project_id}/",
            recursive=True
        )
        
        files = []
        folders = set()
        
        for obj in objects:
            # Пропускаем служебные файлы (.gitkeep)
            if obj.object_name.endswith('.gitkeep'):
                continue
                
            prefix = f"{current_user.unique_id}/{project_id}/"
            relative_path = obj.object_name[len(prefix):] if obj.object_name.startswith(prefix) else obj.object_name
            
            # Если файл в папке images, добавляем его в папку
            if relative_path.startswith("images/"):
                folder_name = "images"
                file_name = relative_path[7:] # len("images/") == 7
            else:
                folder_name = "root"
                file_name = relative_path
            
            # Добавляем папку в список папок
            folders.add(folder_name)
            
            files.append({
                "filename": obj.object_name,
                "original_name": file_name,
                "folder": folder_name,
                "size": obj.size,
                "last_modified": obj.last_modified
            })
        
        return {
            "files": files,
            "folders": list(folders)
        }
        
    except Exception as e:
        logging.error(f"Error getting project files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения файлов проекта: {str(e)}"
        )

@app.get("/api/projects/{project_id}/files/download")
async def download_project_file(
    project_id: int,
    filename: str,
    folder: str = "root",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Скачивание файла проекта (только автор)"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    # Проверяем, что проект принадлежит пользователю
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден или нет прав доступа"
        )
    
    try:
        # Формируем полный путь к файлу
        if folder == "root":
            full_filename = f"{current_user.unique_id}/{project_id}/{filename}"
        else:  # images
            full_filename = f"{current_user.unique_id}/{project_id}/{folder}/{filename}"
        
        # Проверяем, что файл принадлежит проекту пользователя
        if not full_filename.startswith(f"{current_user.unique_id}/{project_id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав доступа к этому файлу"
            )
        
        # Получаем файл из MinIO
        response = minio_client.get_object(BUCKET_NAME, full_filename)
        
        # Определяем MIME-тип по расширению
        file_extension = os.path.splitext(filename)[1].lower()
        mime_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.css': 'text/css',
            '.html': 'text/html',
            '.js': 'application/javascript'
        }
        media_type = mime_type_map.get(file_extension, 'application/octet-stream')
        
        def iterfile():
            try:
                for chunk in response.stream(1024 * 1024):
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл не найден: {str(e)}"
        )

@app.delete("/api/projects/{project_id}/files")
async def delete_project_file(
    project_id: int,
    filename: str,
    folder: str = "root",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление файла проекта (только автор)"""
    if not minio_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис хранения файлов недоступен"
        )
    
    # Проверяем, что проект принадлежит пользователю
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден или нет прав доступа"
        )
    
    try:
        # Формируем полный путь к файлу
        if folder == "root":
            full_filename = f"{current_user.unique_id}/{project_id}/{filename}"
        else:  # images
            full_filename = f"{current_user.unique_id}/{project_id}/{folder}/{filename}"
        
        # Проверяем, что файл принадлежит проекту пользователя
        if not full_filename.startswith(f"{current_user.unique_id}/{project_id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав доступа к этому файлу"
            )
        
        # Удаляем файл из MinIO
        minio_client.remove_object(BUCKET_NAME, full_filename)
        
        # Отключаем хостинг при удалении файлов
        project.is_active = False
        db.commit()
        
        return {"message": f"Файл {filename} успешно удален из папки {folder}"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления файла: {str(e)}"
        )

# Хостинг сайтов
@app.get("/api/projects/{project_id}/hosting")
async def get_project_hosting_info(
    project_id: int,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о хостинге проекта"""
    response.headers["Cache-Control"] = "no-cache"
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Получаем файлы сайта
    site_files = get_site_files_from_minio(current_user.unique_id, project_id)
    
    return {
        "project": project,
        "site_files": site_files,
        "site_url": f"{SITE_PROTOCOL}://{project.subdomain}.{DOMAIN}" if project.subdomain else None
    }

@app.put("/api/projects/{project_id}/hosting")
async def update_project_hosting(
    project_id: int,
    config: SiteHostingConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление настроек хостинга проекта"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    # Проверяем уникальность поддомена, если он изменился
    if config.subdomain != project.subdomain:
        is_unique, message = validate_subdomain_unique(config.subdomain, db, project_id)
        if not is_unique:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
    
    # Обновляем настройки
    project.subdomain = config.subdomain
    project.visibility = config.visibility
    project.is_active = config.is_active
    project.index_file = config.index_file
    
    db.commit()
    db.refresh(project)
    
    return {
        "message": "Настройки хостинга обновлены",
        "project": project,
        "site_url": f"{SITE_PROTOCOL}://{project.subdomain}.{DOMAIN}" if project.subdomain else None
    }

@app.get("/api/projects/{project_id}/hosting/files")
async def get_site_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение файлов сайта"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    site_files = get_site_files_from_minio(current_user.unique_id, project_id)
    return {"files": site_files}

@app.get("/api/sites/{subdomain}")
async def get_site_by_subdomain(
    subdomain: str, 
    request: Request,
    response: Response, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Получение информации о сайте по поддомену (публичный доступ)"""
    response.headers["Cache-Control"] = "no-cache"
    project = db.query(Project).filter(
        Project.subdomain == subdomain,
        Project.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сайт не найден или неактивен"
        )
    
    # Проверка прав доступа для приватных сайтов
    if project.visibility == "PRIVATE":
        if not current_user or current_user.id != project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к этому сайту ограничен"
            )
    
    # Записываем визит (так как это запрос информации о сайте, считаем за просмотр)
    record_project_visit(project, request, db)

    # Получаем файлы сайта
    site_files = get_site_files_from_minio(project.owner.unique_id, project.id)
    
    return {
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "subdomain": project.subdomain,
            "visibility": project.visibility,
            "index_file": project.index_file,
            "owner": {
                "nickname": project.owner.nickname,
                "unique_id": project.owner.unique_id
            }
        },
        "site_files": site_files
    }

@app.get("/api/sites/{subdomain}/{filename:path}")
async def serve_site_file_by_subdomain(
    subdomain: str, 
    filename: str, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Отдача файлов сайта по поддомену"""
    project = db.query(Project).filter(
        Project.subdomain == subdomain,
        Project.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сайт не найден или неактивен"
        )
    
    # Проверка прав доступа для приватных сайтов
    if project.visibility == "PRIVATE":
        if not current_user or current_user.id != project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к этому сайту ограничен"
            )
    
    # Если файл не указан, используем index_file
    if not filename or filename == "":
        filename = project.index_file
    
    # Записываем визит только если запрашивается HTML файл (страница)
    # Чтобы не накручивать счетчик на каждый CSS/JS/IMG
    if filename.lower().endswith(('.html', '.htm')):
        record_project_visit(project, request, db)
    
    return serve_site_file(project.owner.unique_id, project.id, filename)

@app.get("/api/sites/{subdomain}/")
async def serve_site_index_by_subdomain(
    subdomain: str, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Отдача главной страницы сайта по поддомену"""
    project = db.query(Project).filter(
        Project.subdomain == subdomain,
        Project.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сайт не найден или неактивен"
        )
    
    # Проверка прав доступа для приватных сайтов
    if project.visibility == "PRIVATE":
        if not current_user or current_user.id != project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к этому сайту ограничен"
            )
    
    # Записываем визит (главная страница)
    record_project_visit(project, request, db)
    
    return serve_site_file(project.owner.unique_id, project.id, project.index_file)

@app.get("/api/hosting/check-subdomain/{subdomain}")
async def check_subdomain_availability(subdomain: str, db: Session = Depends(get_db)):
    """Проверка доступности поддомена"""
    is_unique, message = validate_subdomain_unique(subdomain, db)
    return {
        "available": is_unique,
        "message": message
    }

# Статистика
@app.get("/api/projects/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики по проекту (только для владельца)"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(weeks=1)
    month_ago = now - timedelta(days=30)
    
    # Базовый запрос
    query = db.query(ProjectVisit).filter(ProjectVisit.project_id == project_id)
    
    # Агрегация по времени
    total_visits = query.count()
    visits_today = query.filter(ProjectVisit.timestamp >= day_ago).count()
    visits_week = query.filter(ProjectVisit.timestamp >= week_ago).count()
    visits_month = query.filter(ProjectVisit.timestamp >= month_ago).count()
    
    # Агрегация по странам
    countries_data = {}
    countries_query = db.query(
        ProjectVisit.country_code, func.count(ProjectVisit.id)
    ).filter(
        ProjectVisit.project_id == project_id
    ).group_by(ProjectVisit.country_code).all()
    
    for country, count in countries_query:
        countries_data[country] = count
        
    # Агрегация по источникам
    sources_data = {}
    sources_query = db.query(
        ProjectVisit.source_type, func.count(ProjectVisit.id)
    ).filter(
        ProjectVisit.project_id == project_id
    ).group_by(ProjectVisit.source_type).all()
    
    for source, count in sources_query:
        sources_data[source] = count
        
    return {
        "total_visits": total_visits,
        "visits_today": visits_today,
        "visits_week": visits_week,
        "visits_month": visits_month,
        "countries": countries_data,
        "sources": sources_data
    }

@app.get("/api/user/stats", response_model=List[ProjectStatsSummary])
async def get_user_projects_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение сводной статистики по всем проектам пользователя"""
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    
    stats_summary = []
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    
    for project in projects:
        total_visits = db.query(ProjectVisit).filter(ProjectVisit.project_id == project.id).count()
        visits_today = db.query(ProjectVisit).filter(
            ProjectVisit.project_id == project.id,
            ProjectVisit.timestamp >= day_ago
        ).count()
        
        stats_summary.append({
            "project_id": project.id,
            "project_title": project.title,
            "total_visits": total_visits,
            "visits_today": visits_today
        })
    
    # Сортировка по посещениям (сначала популярные)
    stats_summary.sort(key=lambda x: x["total_visits"], reverse=True)
    
    return stats_summary

# --- ЧАТ БОТ ---

@app.get("/api/chat/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    session_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Получение истории чата"""
    query = db.query(ChatHistory)
    
    if current_user:
        query = query.filter(ChatHistory.user_id == current_user.id)
    elif session_id:
        query = query.filter(ChatHistory.session_id == session_id)
    else:
        return []
        
    return query.order_by(ChatHistory.timestamp).all()

@app.post("/api/chat/send", response_model=ChatMessageResponse)
async def send_chat_message(
    msg_data: ChatMessageCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Отправка сообщения боту и сохранение истории"""
    
    # 1. Сохраняем сообщение пользователя
    user_msg = ChatHistory(
        user_id=current_user.id if current_user else None,
        session_id=msg_data.session_id,
        sender="user",
        message=msg_data.message
    )
    db.add(user_msg)
    db.commit()
    
    # 2. Отправляем запрос в AI сервис
    bot_reply_text = "Извините, сервис временно недоступен."
    try:
        async with httpx.AsyncClient() as client:
            # В Docker используем имя сервиса, локально localhost
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/chat",
                json={"message": msg_data.message, "user_id": str(current_user.id) if current_user else msg_data.session_id},
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                bot_reply_text = data.get("reply", "")
            else:
                logging.error(f"AI Service Error: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"AI Connection Error: {e}")
    
    # 3. Сохраняем ответ бота
    bot_msg = ChatHistory(
        user_id=current_user.id if current_user else None,
        session_id=msg_data.session_id,
        sender="bot",
        message=bot_reply_text
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)
    
    return bot_msg

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
