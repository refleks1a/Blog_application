from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

from pydantic.types import conint


class UserOut(BaseModel):
    id: int
    username: str

class CreateUserRequest (BaseModel):
    username: str
    id: int 


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


class PostBase(BaseModel):
    content: str
    

class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    owner: UserOut
    likes: int
    reposts: int
    saves: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class PostOut(BaseModel):
    Post: Post


class CommentBase(BaseModel):
    content: str


class Comment(CommentBase):
    id: int
    post: int
    owner: int
    likes: int
    author_like: bool
    created_at: datetime


class CommentCreate(CommentBase):
    pass


class PostLikeBase(BaseModel):
    post: int


class PostLike(PostLikeBase):
    id: int
    owner: int
    created_at: datetime


class PostLikeCreate(PostLikeBase):
    pass
