from fastapi import FastAPI, HTTPException, Depends, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import re
import string
import random

from database import SessionLocal, engine
from models import Base, User, Project
from schemas import (
    UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    ProjectCreate, ProjectResponse, UserWithProjects, UserSearchResult, Token
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
    # Получаем токен из заголовка Authorization
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
        secure=False,  # В продакшене должно быть True
        samesite="lax",
        max_age=1800  # 30 минут
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



