from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class VisibilityType(enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    LINK_ONLY = "link_only"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(10), index=True, unique=True, nullable=False)
    nickname = Column(String(20), index=True, nullable=False)
    email = Column(String(100), index=True, unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(Text, nullable=True)  # Будем хранить base64 изображение
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с проектами
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Новые поля для хостинга сайтов
    subdomain = Column(String(50), index=True, unique=True, nullable=True)  # Поддомен сайта
    visibility = Column(String(20), default="PRIVATE", nullable=False)  # Видимость сайта
    is_active = Column(Boolean, default=False, nullable=False)  # Активен ли сайт
    custom_domain = Column(String(100), nullable=True)  # Кастомный домен (для будущего)
    index_file = Column(String(100), default="index.html", nullable=False)  # Главный файл сайта
    
    # Связь с пользователем
    owner = relationship("User", back_populates="projects")
