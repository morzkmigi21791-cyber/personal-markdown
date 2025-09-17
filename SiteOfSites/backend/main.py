from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends, Response, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from typing import Optional, List, Dict, Annotated
from sqlalchemy.orm import Session

app = FastAPI()

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer()



