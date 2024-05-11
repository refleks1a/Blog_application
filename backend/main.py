from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated

from starlette import status 

from sqlalchemy.orm import Session

from pydantic import BaseModel

import requests

import os

from dotenv import load_dotenv

import models 
import auth
from auth import get_current_user
from database import engine, sessionLocal


load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

models.Base.metadata.create_all(bind=engine)


class User(BaseModel):
    username: str


def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close()    


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends (get_current_user)]


@app.post('/authenticate')
async def authenticate(user: User):
    response = requests.put('https://api.chatengine.io/users/',
        data={
            "username": user.username,
            "secret": user.username,
            "first_name": user.username,
        },
        headers={ "Private-Key": PRIVATE_KEY }
    )

    return response.json()


@app.post("/user", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return user
    
