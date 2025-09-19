from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

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
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
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
