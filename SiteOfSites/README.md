# Site of Sites

Веб-приложение с аутентификацией пользователей на React и FastAPI.

## Структура проекта

- `backend/` - FastAPI бэкенд с PostgreSQL
- `frontend/` - React фронтенд

## Функциональность

✅ **Главная страница** с приветствием "Добро пожаловать"  
✅ **Модальные окна** для регистрации и входа (не отдельные страницы)  
✅ **JWT токены** и HTTP-only куки для безопасности  
✅ **Валидация форм**: правильность email, совпадение паролей, длина никнейма  
✅ **Автоматический вход** после регистрации  
✅ **Управление состоянием**: кнопки регистрации/входа исчезают после входа  
✅ **Профиль пользователя** с выпадающим меню (личный кабинет, выход)  

## Быстрый запуск

### 1. Настройка базы данных

Создайте базу данных в PostgreSQL:
```sql
-- Подключитесь к PostgreSQL
psql -U postgres

-- Создайте базу данных
CREATE DATABASE siteofsites;

-- Выйдите
\q
```

### 2. Настройка проекта

1. **Скопируйте файл конфигурации:**
```bash
cd backend
copy env_example.txt .env
```

2. **Отредактируйте .env файл:**
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=ваш_пароль_от_postgres
DB_NAME=siteofsites
```

### 3. Запуск

**Бэкенд:**
```bash
cd backend
pip install -r requirements.txt
python init_db.py  # Создание таблиц
python run.py      # Запуск сервера
```

**Фронтенд:**
```bash
cd frontend
npm install
npm start
```

## Быстрый запуск (Windows)

Просто запустите:
```bash
start.bat
```

Этот скрипт автоматически запустит и бэкенд, и фронтенд.

## Альтернативный запуск

Можно использовать отдельные bat-файлы:

- `backend/start.bat` - запуск бэкенда
- `frontend/start.bat` - запуск фронтенда

## API Endpoints

- `POST /api/auth/register` - регистрация пользователя
- `POST /api/auth/login` - вход в систему  
- `GET /api/auth/me` - получение информации о текущем пользователе
- `POST /api/auth/logout` - выход из системы

## Технологии

**Backend:**
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT (python-jose)
- Argon2 для хеширования паролей

**Frontend:**
- React 18
- Axios для HTTP запросов
- CSS для стилизации
- Модальные окна
