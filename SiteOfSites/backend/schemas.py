from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class VisibilityType(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    LINK_ONLY = "link_only"

class UserBase(BaseModel):
    email: str
    nickname: str

class UserCreate(UserBase):
    password: str
    confirm_password: str
    
    @validator('email')
    def validate_email(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Некорректный email адрес')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if len(v) < 2:
            raise ValueError('Никнейм должен содержать минимум 2 символа')
        if len(v) > 20:
            raise ValueError('Никнейм не должен превышать 20 символов')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    unique_id: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if v is not None:
            if len(v) < 2:
                raise ValueError('Никнейм должен содержать минимум 2 символа')
            if len(v) > 20:
                raise ValueError('Никнейм не должен превышать 20 символов')
        return v

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    subdomain: Optional[str] = None
    visibility: str = "PRIVATE"
    is_active: bool = False
    index_file: str = "index.html"
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if v is not None:
            import re
            # Разрешаем только буквы, цифры и дефисы, длина 3-50 символов
            pattern = r'^[a-zA-Z0-9-]{3,50}$'
            if not re.match(pattern, v):
                raise ValueError('Поддомен может содержать только буквы, цифры и дефисы (3-50 символов)')
            if v.startswith('-') or v.endswith('-'):
                raise ValueError('Поддомен не может начинаться или заканчиваться дефисом')
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ['PRIVATE', 'PUBLIC', 'LINK_ONLY']:
            raise ValueError('Видимость должна быть PRIVATE, PUBLIC или LINK_ONLY')
        return v

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subdomain: Optional[str] = None
    visibility: Optional[str] = None
    is_active: Optional[bool] = None
    index_file: Optional[str] = None
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if v is not None:
            import re
            # Разрешаем только буквы, цифры и дефисы, длина 3-50 символов
            pattern = r'^[a-zA-Z0-9-]{3,50}$'
            if not re.match(pattern, v):
                raise ValueError('Поддомен может содержать только буквы, цифры и дефисы (3-50 символов)')
            if v.startswith('-') or v.endswith('-'):
                raise ValueError('Поддомен не может начинаться или заканчиваться дефисом')
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        if v is not None and v not in ['PRIVATE', 'PUBLIC', 'LINK_ONLY']:
            raise ValueError('Видимость должна быть PRIVATE, PUBLIC или LINK_ONLY')
        return v

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    subdomain: Optional[str] = None
    visibility: str
    is_active: bool
    custom_domain: Optional[str] = None
    index_file: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithProjects(UserResponse):
    projects: List[ProjectResponse] = []

class UserSearchResult(BaseModel):
    id: int
    unique_id: str
    nickname: str
    avatar: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class SiteHostingConfig(BaseModel):
    subdomain: str
    visibility: str
    is_active: bool
    index_file: str = "index.html"
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9-]{3,50}$'
        if not re.match(pattern, v):
            raise ValueError('Поддомен может содержать только буквы, цифры и дефисы (3-50 символов)')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Поддомен не может начинаться или заканчиваться дефисом')
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ['PRIVATE', 'PUBLIC', 'LINK_ONLY']:
            raise ValueError('Видимость должна быть PRIVATE, PUBLIC или LINK_ONLY')
        return v
