from datetime import timedelta, datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from starlette import status 

from pydantic import BaseModel

from database import sessionLocal 
from models import User, Post, PostComment
import schemas
import auth

import os

from dotenv import load_dotenv


load_dotenv()

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: schemas.CreateUserRequest = Depends(auth.get_current_user)):

    new_post = Post(owner_id=current_user["id"], **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):

    posts = db.query(Post, func.count(PostComment.post).label("post_comments")).join(
        PostComment, PostComment.post == Post.id, isouter=True).group_by(Post.id).filter(Post.content.contains(search)).limit(limit).offset(skip).all()
    
    return posts


@router.get("/{id}", response_model=schemas.PostOut)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):

    post = db.query(Post, func.count(PostComment.post).label("post_comments")).join(
        PostComment, PostComment.post == Post.id, isouter=True).group_by(Post.id).filter(Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")

    return post  


@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):

    post_query = db.query(Post).filter(Post.id == id)

    post = post_query.first()

    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    if post.owner_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    post_query.update(updated_post.dict(), synchronize_session=False)

    db.commit()

    return post_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):

    post_query = db.query(Post).filter(Post.id == id)

    post = post_query.first()

    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    if post.owner_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    post_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

