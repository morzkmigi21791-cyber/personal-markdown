# Техническая документация - Site of Sites

## Содержание
1. [Архитектура системы](#архитектура-системы)
2. [База данных](#база-данных)
3. [API Endpoints](#api-endpoints)
4. [Алгоритмы поиска](#алгоритмы-поиска)
5. [Система аутентификации](#система-аутентификации)
6. [Frontend архитектура](#frontend-архитектура)
7. [Роутинг и навигация](#роутинг-и-навигация)
8. [Компоненты UI](#компоненты-ui)
9. [Обработка ошибок](#обработка-ошибок)
10. [Производительность](#производительность)

---

## Архитектура системы

### Backend (FastAPI + SQLAlchemy)
- **Framework**: FastAPI для REST API
- **ORM**: SQLAlchemy для работы с базой данных
- **База данных**: SQLite (встроенная)
- **Аутентификация**: JWT токены
- **CORS**: Настроен для работы с frontend

### Frontend (React + React Router)
- **Framework**: React 18
- **Роутинг**: React Router DOM v6
- **HTTP клиент**: Axios
- **Стили**: CSS модули
- **Состояние**: React Hooks (useState, useEffect)

### Связь Frontend-Backend
- **Proxy**: Настроен в package.json (`"proxy": "http://localhost:8000"`)
- **CORS**: Разрешен для localhost:3000
- **Токены**: Хранятся в localStorage
- **Куки**: Используются для дополнительной безопасности

---

## База данных

### Таблица `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    unique_id VARCHAR(10) UNIQUE NOT NULL,
    nickname VARCHAR(20) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar TEXT,  -- base64 encoded image
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Индексы:**
- `unique_id` - для быстрого поиска по ID
- `nickname` - для поиска по имени
- `email` - для аутентификации

### Таблица `projects`
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

**Связи:**
- `owner_id` → `users.id` (один ко многим)

---

## API Endpoints

### Аутентификация

#### POST `/api/auth/register`
**Описание**: Регистрация нового пользователя
**Тело запроса**:
```json
{
    "email": "user@example.com",
    "nickname": "username",
    "password": "password123",
    "confirm_password": "password123"
}
```
**Валидация**:
- Email: regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Пароль: минимум 6 символов
- Никнейм: 2-20 символов
- Подтверждение пароля должно совпадать

**Процесс**:
1. Проверка уникальности email и nickname
2. Генерация уникального ID (5-10 символов)
3. Хеширование пароля (bcrypt)
4. Создание пользователя в БД
5. Генерация JWT токена
6. Возврат токена и данных пользователя

#### POST `/api/auth/login`
**Описание**: Вход в систему
**Тело запроса**:
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```
**Процесс**:
1. Поиск пользователя по email
2. Проверка пароля (bcrypt.verify)
3. Генерация JWT токена
4. Установка HTTP-only куки
5. Возврат токена и данных пользователя

#### GET `/api/auth/me`
**Описание**: Получение информации о текущем пользователе
**Заголовки**: `Authorization: Bearer {token}`
**Процесс**:
1. Валидация JWT токена
2. Извлечение email из payload
3. Поиск пользователя в БД
4. Возврат данных пользователя

### Поиск пользователей

#### GET `/api/users/search?q={query}`
**Описание**: Поиск пользователей по имени или уникальному ID
**Параметры**:
- `q` (string): поисковый запрос (минимум 2 символа)

**Алгоритм поиска**:
```python
# SQL запрос с ILIKE для регистронезависимого поиска
users = db.query(User).filter(
    (User.nickname.ilike(f"%{q}%")) | (User.unique_id.ilike(f"%{q}%"))
).limit(5).all()
```

**Особенности**:
- Частичное совпадение (LIKE с %)
- Регистронезависимый поиск (ILIKE)
- Поиск по двум полям одновременно (OR)
- Ограничение до 5 результатов
- Возврат только базовой информации (id, unique_id, nickname, avatar)

### Профили пользователей

#### GET `/api/users/by-unique-id/{unique_id}`
**Описание**: Получение профиля по уникальному ID
**Параметры**:
- `unique_id` (string): уникальный ID пользователя

**Возвращаемые данные**:
- Полная информация о пользователе
- Список всех проектов пользователя
- Связанные данные через SQLAlchemy relationships

#### GET `/api/users/{user_id}`
**Описание**: Получение профиля по внутреннему ID
**Аналогично предыдущему, но по числовому ID**

#### PUT `/api/users/profile`
**Описание**: Обновление профиля текущего пользователя
**Заголовки**: `Authorization: Bearer {token}`
**Тело запроса**:
```json
{
    "nickname": "new_nickname",
    "description": "New description",
    "avatar": "data:image/jpeg;base64,..."
}
```

**Валидация**:
- Никнейм: проверка уникальности (исключая текущего пользователя)
- Все поля опциональны (partial update)

### Управление проектами

#### GET `/api/projects`
**Описание**: Получение проектов текущего пользователя
**Заголовки**: `Authorization: Bearer {token}`
**Фильтрация**: `WHERE owner_id = current_user.id`

#### POST `/api/projects`
**Описание**: Создание нового проекта
**Тело запроса**:
```json
{
    "title": "Project Title",
    "description": "Project description"
}
```

#### PUT `/api/projects/{project_id}`
**Описание**: Обновление проекта
**Проверка прав**: `WHERE owner_id = current_user.id AND id = project_id`

#### DELETE `/api/projects/{project_id}`
**Описание**: Удаление проекта
**Проверка прав**: аналогично PUT

---

## Алгоритмы поиска

### Генерация уникального ID
```python
def generate_unique_id(db: Session) -> str:
    while True:
        length = random.randint(5, 10)
        unique_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
        # Проверка уникальности
        if not db.query(User).filter(User.unique_id == unique_id).first():
            return unique_id
```

**Особенности**:
- Случайная длина от 5 до 10 символов
- Только буквы (a-z, A-Z) и цифры (0-9)
- Проверка уникальности в БД
- Бесконечный цикл до нахождения уникального ID

### Поиск пользователей
```python
# SQL запрос
users = db.query(User).filter(
    (User.nickname.ilike(f"%{q}%")) | (User.unique_id.ilike(f"%{q}%"))
).limit(5).all()
```

**Алгоритм**:
1. **Входные данные**: поисковый запрос `q`
2. **Минимальная длина**: 2 символа (проверка на frontend)
3. **Поиск по полям**: nickname ИЛИ unique_id
4. **Тип поиска**: частичное совпадение (LIKE %query%)
5. **Регистр**: игнорируется (ILIKE)
6. **Лимит**: 5 результатов
7. **Сортировка**: по умолчанию (порядок вставки)

**Примеры запросов**:
- `"john"` → найдет "john_doe", "johnny", "john123"
- `"abc"` → найдет "abc123", "my_abc", "ABCdef"
- `"123"` → найдет "user123", "123abc", "test123"

---

## Система аутентификации

### JWT Токены
**Алгоритм**: HS256
**Секретный ключ**: хранится в переменных окружения
**Время жизни**: 30 минут
**Payload**:
```json
{
    "sub": "user@example.com",  // email пользователя
    "exp": 1234567890,          // время истечения
    "iat": 1234567890           // время создания
}
```

### Хеширование паролей
**Алгоритм**: bcrypt
**Соль**: автоматическая генерация
**Раунды**: 12 (по умолчанию)

```python
# Хеширование
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Проверка
is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash)
```

### Middleware аутентификации
```python
def get_current_user(request: Request, db: Session = Depends(get_db)):
    # 1. Извлечение токена из заголовка Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Токен не предоставлен")
    
    token = auth_header.split(" ")[1]
    
    # 2. Валидация JWT токена
    try:
        payload = verify_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(401, "Недействительный токен")
    except Exception:
        raise HTTPException(401, "Недействительный токен")
    
    # 3. Поиск пользователя в БД
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(401, "Пользователь не найден")
    
    return user
```

---

## Frontend архитектура

### Структура компонентов
```
src/
├── App.js                 # Главный компонент с роутингом
├── components/
│   ├── Header.js          # Шапка с поиском и меню
│   ├── SearchBar.js       # Компонент поиска
│   ├── ProfileDropdown.js # Выпадающее меню профиля
│   ├── LoginModal.js      # Модальное окно входа
│   └── RegisterModal.js   # Модальное окно регистрации
├── pages/
│   ├── UserProfilePage.js # Страница просмотра профиля
│   └── ProfileSettingsPage.js # Страница настроек
└── App.css               # Глобальные стили
```

### Управление состоянием
**Глобальное состояние** (App.js):
- `user` - текущий пользователь
- `showLoginModal` - показ модального окна входа
- `showRegisterModal` - показ модального окна регистрации
- `loading` - состояние загрузки

**Локальное состояние** (компоненты):
- `formData` - данные форм
- `searchResults` - результаты поиска
- `isOpen` - состояние выпадающих меню

### HTTP клиент (Axios)
```javascript
// Настройка
axios.defaults.withCredentials = true;

// Запросы с токеном
const token = localStorage.getItem('access_token');
const response = await axios.get('/api/endpoint', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## Роутинг и навигация

### React Router конфигурация
```javascript
<Router>
  <Routes>
    <Route path="/" element={<Welcome />} />
    <Route path="/profile/:uniqueId" element={<UserProfilePage />} />
    <Route path="/settings" element={<ProfileSettingsPage />} />
  </Routes>
</Router>
```

### Навигационные функции
```javascript
const navigate = useNavigate();

// Переход к профилю пользователя
const handleUserSelect = (selectedUser) => {
  navigate(`/profile/${selectedUser.unique_id}`);
};

// Переход к настройкам
const handleSettingsClick = () => {
  navigate('/settings');
};
```

### URL структура
- `/` - главная страница
- `/profile/{unique_id}` - профиль пользователя
- `/settings` - настройки профиля

---

## Компоненты UI

### SearchBar
**Функциональность**:
- Debounced поиск (300ms задержка)
- Автозакрытие при клике вне области
- Показ результатов в реальном времени
- Обработка состояний загрузки

**Алгоритм debounce**:
```javascript
useEffect(() => {
  const timeoutId = setTimeout(() => {
    if (query.length >= 2) {
      performSearch(query);
    }
  }, 300);
  
  return () => clearTimeout(timeoutId);
}, [query]);
```

**Обработка клика вне области**:
```javascript
useEffect(() => {
  const handleClickOutside = (event) => {
    if (searchRef.current && !searchRef.current.contains(event.target)) {
      setShowResults(false);
    }
  };
  
  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
}, []);
```

### UserProfilePage
**Параметры URL**: `useParams()` для получения `uniqueId`
**Загрузка данных**: `useEffect` при изменении `uniqueId`
**Обработка ошибок**: 404 для несуществующих пользователей
**Условный рендеринг**: кнопка настроек только для владельца

### ProfileSettingsPage
**Защита маршрута**: проверка авторизации
**Управление формами**: controlled components
**Загрузка файлов**: FileReader для конвертации в base64
**CRUD операции**: создание, чтение, обновление, удаление проектов

---

## Обработка ошибок

### Backend
**HTTP статус коды**:
- `200` - успешный запрос
- `400` - ошибка валидации
- `401` - неавторизован
- `404` - ресурс не найден
- `500` - внутренняя ошибка сервера

**Структура ошибок**:
```json
{
  "detail": "Описание ошибки"
}
```

**Обработка исключений**:
```python
try:
    # Логика
    pass
except ValidationError as e:
    raise HTTPException(400, detail=str(e))
except Exception as e:
    raise HTTPException(500, detail="Внутренняя ошибка сервера")
```

### Frontend
**Обработка HTTP ошибок**:
```javascript
try {
  const response = await axios.get('/api/endpoint');
  setData(response.data);
} catch (error) {
  setError(error.response?.data?.detail || 'Ошибка загрузки');
}
```

**Пользовательские уведомления**:
- Успех: зеленые alert с сообщением
- Ошибка: красные alert с описанием
- Загрузка: спиннеры и disabled состояния

---

## Производительность

### Backend оптимизации
**Индексы БД**:
- `unique_id` - для быстрого поиска по ID
- `nickname` - для поиска по имени
- `email` - для аутентификации

**Лимиты запросов**:
- Поиск: максимум 5 результатов
- Пагинация: не реализована (для будущих версий)

**Кэширование**:
- Не реализовано (для будущих версий)
- JWT токены: stateless, не требуют кэша

### Frontend оптимизации
**Debounced поиск**:
- 300ms задержка для уменьшения запросов
- Очистка таймаутов при размонтировании

**Мемоизация**:
- Не используется (для будущих версий)
- React.memo для компонентов (для будущих версий)

**Lazy loading**:
- Не реализован (для будущих версий)
- Code splitting (для будущих версий)

### Размер данных
**Аватарки**:
- Хранение в base64 в БД
- Ограничение размера на frontend
- Сжатие не реализовано (для будущих версий)

**Проекты**:
- Текстовые поля без ограничений
- Валидация длины на frontend и backend

---

## Безопасность

### Backend
**Валидация входных данных**:
- Pydantic схемы для всех endpoints
- Regex для email
- Ограничения длины для всех полей

**SQL инъекции**:
- SQLAlchemy ORM предотвращает SQL инъекции
- Параметризованные запросы

**XSS защита**:
- Экранирование HTML в шаблонах
- Content Security Policy (для будущих версий)

### Frontend
**XSS защита**:
- React автоматически экранирует JSX
- Осторожность с dangerouslySetInnerHTML

**CSRF защита**:
- SameSite cookies
- CORS настройки

**Хранение токенов**:
- localStorage (не HTTP-only)
- Рекомендация: использовать HTTP-only cookies

---

## Мониторинг и логирование

### Backend
**Логирование**:
- Стандартное логирование Python
- Логи ошибок в консоль

**Метрики**:
- Не реализованы (для будущих версий)
- Prometheus + Grafana (для будущих версий)

### Frontend
**Логирование**:
- console.log для отладки
- console.error для ошибок

**Мониторинг**:
- Не реализован (для будущих версий)
- Sentry для отслеживания ошибок (для будущих версий)

---

## Развертывание

### Backend
**Зависимости**: `requirements.txt`
**Запуск**: `python main.py`
**Порт**: 8000
**База данных**: SQLite (файл)

### Frontend
**Зависимости**: `package.json`
**Запуск**: `npm start`
**Порт**: 3000
**Сборка**: `npm run build`

### Переменные окружения
**Backend**:
- `SECRET_KEY` - для JWT токенов
- `DATABASE_URL` - для подключения к БД

**Frontend**:
- `REACT_APP_API_URL` - URL backend API

---

## Будущие улучшения

### Backend
- [ ] Пагинация для поиска
- [ ] Кэширование (Redis)
- [ ] Логирование в файлы
- [ ] Метрики производительности
- [ ] Rate limiting
- [ ] Валидация размера аватарок

### Frontend
- [ ] Lazy loading компонентов
- [ ] Мемоизация (React.memo)
- [ ] Виртуализация списков
- [ ] PWA функциональность
- [ ] Офлайн режим

### Общие
- [ ] Docker контейнеризация
- [ ] CI/CD пайплайн
- [ ] Автоматическое тестирование
- [ ] Мониторинг и алерты
- [ ] Backup стратегия
