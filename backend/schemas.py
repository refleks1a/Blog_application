from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

from pydantic.types import conint


class PostBase(BaseModel):
    content: str
    


class PostCreate(PostBase):
    pass


class UserOut(BaseModel):
    id: int
    username: str


class Post(PostBase):
    id: int
    owner: UserOut
    likes: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class PostOut(BaseModel):
    Post: Post


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
