from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends
from typing import Optional, List, Dict, Annotated
from sqlalchemy.orm import Session

from fastapi.middleware.cors import CORSMiddleware
from models import Base, User, Post
from database import engine, session_local
from schemas import  UserCreate, User as DbUser, PostCreate, PostResponse
from schemas import UserAuth
from security import hash_password, verify_password


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

@app.post("/login", response_model=DbUser)
async def login(auth: UserAuth, db: Session = Depends(get_db)) -> DbUser:
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

    return db_user

@app.post("/posts/", response_model=PostResponse)
async def create_post(post: PostCreate, db: Session = Depends(get_db)) -> PostResponse:
    db_user = db.query(User).filter(User.id == post.author_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_post = Post(title=post.title, body=post.body, author_id=post.author_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(db: Session = Depends(get_db)):
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