from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    age = Column(Integer, nullable=False)
    email = Column(String(255), index=True, unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Связь с постами
    posts = relationship('Post', back_populates='author')


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text(1000), nullable=False)  # Ограничение на 1000 символов
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship('User', back_populates='posts')