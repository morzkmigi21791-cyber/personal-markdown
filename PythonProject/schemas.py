from pydantic import BaseModel, EmailStr, conint, constr, Field
from typing import Optional
from datetime import datetime
import json


class UserBase(BaseModel):
    name: str
    age: conint(ge=0)
    email: EmailStr


class UserCreate(UserBase):
    password: constr(min_length=6)


class UserAuth(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class PostCreate(BaseModel):
    content: constr(min_length=1, max_length=1000)


class PostResponse(BaseModel):
    id: int
    content: str
    author_id: int
    created_at: datetime
    author: User

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }