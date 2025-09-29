from fastapi import FastAPI, HTTPException, Depends, Response, status, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
import re
import string
import random

from starlette.responses import StreamingResponse

from s3 import minio_client, BUCKET_NAME
import io
import os
from config import ALLOWED_FILE_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_FILE_SIZE


from database import SessionLocal, engine
from models import Base, User, Project
from schemas import (
    UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    ProjectCreate, ProjectUpdate, ProjectResponse,
    UserWithProjects, UserSearchResult, Token, SiteHostingConfig
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

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency для получения текущего пользователя
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    # Получение токена из заголовка Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не предоставлен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    try:
        payload = verify_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from models import User
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
            # Пропускаем файлы из папки images и служебные файлы
            if not obj.object_name.startswith(f"{user_unique_id}/{project_id}/images/") and not obj.object_name.endswith('.gitkeep'):
                relative_path = obj.object_name.replace(f"{user_unique_id}/{project_id}/", "")
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
        
        return StreamingResponse(
            response,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл не найден: {str(e)}"
        )

@app.get("/")
async def root():
    return {"message": "Site of Sites API"}

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
    access_token_expires = timedelta(minutes=30)
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
    access_token_expires = timedelta(minutes=30)
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
        max_age=1800
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение проектов текущего пользователя"""
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
        
        return StreamingResponse(
            response,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка файлов проекта (только автор)"""
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
                
            relative_path = obj.object_name.replace(f"{current_user.unique_id}/{project_id}/", "")
            
            # Если файл в папке images, добавляем его в папку
            if relative_path.startswith("images/"):
                folder_name = "images"
                file_name = relative_path.replace("images/", "")
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
        
        return StreamingResponse(
            response,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о хостинге проекта"""
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
        "site_url": f"http://{project.subdomain}.siteofsites.local" if project.subdomain else None
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
        "site_url": f"http://{project.subdomain}.siteofsites.local" if project.subdomain else None
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
async def get_site_by_subdomain(subdomain: str, db: Session = Depends(get_db)):
    """Получение информации о сайте по поддомену (публичный доступ)"""
    project = db.query(Project).filter(
        Project.subdomain == subdomain,
        Project.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сайт не найден или неактивен"
        )
    
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
    db: Session = Depends(get_db)
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
    
    # Если файл не указан, используем index_file
    if not filename or filename == "":
        filename = project.index_file
    
    return serve_site_file(project.owner.unique_id, project.id, filename)

@app.get("/api/sites/{subdomain}/")
async def serve_site_index_by_subdomain(
    subdomain: str, 
    db: Session = Depends(get_db)
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
    
    return serve_site_file(project.owner.unique_id, project.id, project.index_file)

@app.get("/api/hosting/check-subdomain/{subdomain}")
async def check_subdomain_availability(subdomain: str, db: Session = Depends(get_db)):
    """Проверка доступности поддомена"""
    is_unique, message = validate_subdomain_unique(subdomain, db)
    return {
        "available": is_unique,
        "message": message
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



