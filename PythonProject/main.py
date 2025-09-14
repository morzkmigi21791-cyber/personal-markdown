from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends, Response, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Annotated
from sqlalchemy.orm import Session
from datetime import timedelta

from fastapi.middleware.cors import CORSMiddleware
from models import Base, User, Post
from database import engine, session_local
from schemas import UserCreate, User as DbUser, PostCreate, PostResponse, UserAuth, Token, TokenData
from security import hash_password, verify_password, create_access_token, verify_token, encrypt_cookie, decrypt_cookie


app = FastAPI()

origins = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://192.168.1.87:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()


# Security
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token (optional)."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if payload is None:
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        return user
    except:
        return None


@app.post("/users", response_model=DbUser)
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> DbUser:
    # Check uniqueness by email/login
    existing = db.query(User).filter(User.email == user.email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email is already registered")

    hashed = hash_password(user.password)

    db_user = User(name=user.name, age=user.age, email=user.email)

    if hasattr(User, 'password_hash'):
        setattr(db_user, 'password_hash', hashed)
    elif hasattr(User, 'password'):
        setattr(db_user, 'password', hashed)
    else:
        raise HTTPException(status_code=500, detail="User model has no password field")

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/register", response_model=DbUser)
async def register(user: UserCreate, db: Session = Depends(get_db)) -> DbUser:
    existing = db.query(User).filter(User.email == user.email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email is already registered")

    hashed = hash_password(user.password)

    db_user = User(name=user.name, age=user.age, email=user.email)
    if hasattr(User, 'password_hash'):
        setattr(db_user, 'password_hash', hashed)
    elif hasattr(User, 'password'):
        setattr(db_user, 'password', hashed)
    else:
        raise HTTPException(status_code=500, detail="User model has no password field")

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login(auth: UserAuth, response: Response, db: Session = Depends(get_db)) -> Token:
    db_user = db.query(User).filter(User.email == auth.email).first()
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Retrieve stored hash from appropriate field
    stored_hash = None
    if hasattr(User, 'password_hash'):
        stored_hash = getattr(db_user, 'password_hash', None)
    elif hasattr(User, 'password'):
        stored_hash = getattr(db_user, 'password', None)

    if not stored_hash or not verify_password(auth.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    # Create encrypted cookie with user data
    user_data = {
        "id": db_user.id,
        "name": db_user.name,
        "age": db_user.age,
        "email": db_user.email
    }
    import json
    encrypted_cookie = encrypt_cookie(json.dumps(user_data))
    
    # Set encrypted cookie
    response.set_cookie(
        key="userData",
        value=encrypted_cookie,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=DbUser)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.post("/logout")
async def logout(response: Response):
    """Logout user by clearing the cookie."""
    response.delete_cookie(key="userData")
    return {"message": "Successfully logged out"}


@app.get("/auth/check", response_model=DbUser)
async def check_auth(request: Request, db: Session = Depends(get_db)):
    """Check authentication via encrypted cookie."""
    user_data_cookie = request.cookies.get("userData")
    if not user_data_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        decrypted_data = decrypt_cookie(user_data_cookie)
        if not decrypted_data:
            raise HTTPException(status_code=401, detail="Invalid cookie")
        
        import json
        user_data = json.loads(decrypted_data)
        user = db.query(User).filter(User.id == user_data.get("id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication data")


@app.post("/posts/", response_model=PostResponse)
async def create_post(post: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PostResponse:
    db_user = db.query(User).filter(User.id == post.author_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_post = Post(title=post.title, body=post.body, author_id=post.author_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Post).all()

@app.get("/users/{name}", response_model=DbUser)
async def post(name: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.name == name).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# @app.get("/items/")
# async def items() -> List[Post]:
#     return [Post(**post) for post in posts]
#
#
# @app.post("/items/add")
# async def add_item(post: PostCreate) -> Post:
#     author = next((user for user in users if user["id"] == post.author_id), None)
#     if not author:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     new_post_id = len(posts) + 1
#
#     new_post = {'id': new_post_id, 'title': post.title, 'body': post.body, 'author': author}
#     posts.append(new_post)
#
#
#     return Post(**new_post)
#
#
# @app.post("/user/add")
# async def user_add(user: Annotated[
#     UserCreate,
#     Body(..., example={
#         "name": "UserName",
#         "age": 1
#     })
# ]) -> User:
#     new_user_id = len(users) + 1
#
#     new_user = {'id': new_user_id, 'name': user.name, 'age': user.age}
#     user.append(new_user)
#
#
#     return User(**new_user)
#
#
#
# @app.get("/items/{id}")
# async def items(id: Annotated[int, Path(..., title='Здесь указывается id поста', ge=1, lt=100)]) -> dict:
#     for post in posts:
#         if post['id'] == id:
#             return post
#
#     raise HTTPException(status_code=404, detail="Post not found")
#
# @app.get("/search")
# async def search(post_id: Annotated[
#     Optional[int],
#     Query(title="Id of post to search for", ge=1, lt=50),
# ])-> Dict[str, Optional[Post]]:
#     if post_id:
#         for post in posts:
#             if post['id'] == post_id:
#
#                 return {"data": Post(**post)}
#         raise HTTPException(status_code=404, detail="Post not found")
#     else:
#         return {"data": None}