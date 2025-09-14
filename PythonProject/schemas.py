from pydantic import BaseModel, EmailStr, conint, constr
from typing import Optional


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


class PostBase(BaseModel):
    title: str
    body: str
    author_id: int


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    author: User

    class Config:
        orm_mode = True