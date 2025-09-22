from fastapi import FastAPI, HTTPException, Depends, Response, status, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import re
import string
import random

from starlette.responses import StreamingResponse

from s3 import minio_client, BUCKET_NAME
import io
import os
from config import ALLOWED_FILE_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_FILE_SIZE


from database import SessionLocal, engine
from models import Base, User, Project, ProjectFile
from schemas import (
    UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    ProjectCreate, ProjectResponse, ProjectFileResponse, UserWithProjects, UserSearchResult, Token
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
        # Логируем предупреждение, но не блокируем загрузку
        print(f"Предупреждение: Несоответствие MIME-типа для {file.filename}. Ожидается один из: {', '.join(ALLOWED_MIME_TYPES)}, получен: {file.content_type}")
    
    return True, "Файл валиден"

def validate_file_size(file_data: bytes) -> tuple[bool, str]:
    """Проверяет размер файла"""
    if len(file_data) > MAX_FILE_SIZE:
        return False, f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024*1024)}MB"
    return True, "Размер файла допустим"

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
    db_project = Project(
        title=project.title,
        description=project.description,
        owner_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
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
    project: ProjectCreate,
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
    
    db_project.title = project.title
    db_project.description = project.description
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
    """Загрузка файла с валидацией"""
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
        unique_filename = f"{current_user.unique_id}_{file.filename}"
        
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
        if not filename.startswith(f"{current_user.unique_id}_"):
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
                "Content-Disposition": f"attachment; filename={filename}",
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
            prefix=f"{current_user.unique_id}_",
            recursive=True
        )
        
        files = []
        for obj in objects:
            files.append({
                "filename": obj.object_name,
                "original_name": obj.object_name.replace(f"{current_user.unique_id}_", "", 1),
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
        if not filename.startswith(f"{current_user.unique_id}_"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав доступа к этому файлу"
            )
        
        # Удаляем файл из MinIO
        minio_client.remove_object(BUCKET_NAME, filename)
        
        return {"message": f"Файл {filename} успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления файла: {str(e)}"
        )

# Управление файлами проектов
@app.post("/api/projects/{project_id}/files", response_model=ProjectFileResponse)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
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
        unique_filename = f"project_{project_id}_{current_user.unique_id}_{file.filename}"
        
        # Сохраняем в MinIO
        minio_client.put_object(
            BUCKET_NAME,
            unique_filename,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Сохраняем информацию о файле в БД
        db_file = ProjectFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_size=len(file_data),
            content_type=file.content_type or "application/octet-stream",
            project_id=project_id
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return db_file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки файла: {str(e)}"
        )

@app.get("/api/projects/{project_id}/files", response_model=List[ProjectFileResponse])
async def get_project_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка файлов проекта (только автор)"""
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
    
    files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
    return files

@app.get("/api/projects/{project_id}/files/{file_id}/download")
async def download_project_file(
    project_id: int,
    file_id: int,
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
    
    # Получаем информацию о файле
    file_record = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )
    
    try:
        # Получаем файл из MinIO
        response = minio_client.get_object(BUCKET_NAME, file_record.filename)
        
        # Определяем MIME-тип по расширению
        file_extension = os.path.splitext(file_record.original_filename)[1].lower()
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
                "Content-Disposition": f"attachment; filename={file_record.original_filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения файла: {str(e)}"
        )

@app.delete("/api/projects/{project_id}/files/{file_id}")
async def delete_project_file(
    project_id: int,
    file_id: int,
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
    
    # Получаем информацию о файле
    file_record = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )
    
    try:
        # Удаляем файл из MinIO
        minio_client.remove_object(BUCKET_NAME, file_record.filename)
        
        # Удаляем запись из БД
        db.delete(file_record)
        db.commit()
        
        return {"message": f"Файл {file_record.original_filename} успешно удален"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления файла: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



