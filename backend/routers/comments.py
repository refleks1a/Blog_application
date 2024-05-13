from datetime import timedelta, datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from starlette import status 

from pydantic import BaseModel

import database
import models

from database import sessionLocal 
from models import User, Post, PostComment, CommentLike

import schemas
from routers import auth

import os

from dotenv import load_dotenv


load_dotenv()

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)

def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/{post_id}", status_code=status.HTTP_201_CREATED, response_model=schemas.Comment)
def create_comment(post_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: schemas.CreateUserRequest = Depends(auth.get_current_user)):

    new_comment = PostComment(owner=current_user["id"], post=post_id, **comment.dict())
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment


@router.get("/", response_model=List[schemas.Comment])
def get_comments(db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):

    comments = db.query(PostComment).group_by(PostComment.id).filter(PostComment.content.contains(search)).limit(limit).offset(skip).all()
    
    return comments


@router.get("/{id}", response_model=schemas.Comment)
def get_comment(id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):

    comment = db.query(PostComment).group_by(PostComment.id).filter(PostComment.id == id).first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id: {id} was not found")

    return comment  


@router.put("/{id}", response_model=schemas.Comment)
def update_comment(id: int, updated_comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):

    comment_query = db.query(PostComment).filter(PostComment.id == id)

    comment = comment_query.first()

    if comment == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id: {id} does not exist")

    if comment.owner != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    comment_query.update(updated_comment.dict(), synchronize_session=False)

    db.commit()

    return comment_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):

    comment_query = db.query(PostComment).filter(PostComment.id == id)

    comment = comment_query.first()

    if comment == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id: {id} does not exist")

    if comment.owner != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    comment_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/like", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentLike)
def create_like(id: int, db: Session = Depends(get_db),
        current_user: schemas.CreateUserRequest = Depends(auth.get_current_user)):
    # The comment that being liked
    liked_comment = db.query(PostComment).filter(PostComment.id == id).first()

    if liked_comment == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The comment with id: {id} does not exist")
    
    # Check wether like object already exists
    like_query = db.query(CommentLike).group_by(CommentLike.id).filter(
        CommentLike.owner == current_user["id"], CommentLike.comment == id).first()

    if like_query is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You cannot like one comment twice")

    # Create like object
    new_like = CommentLike(owner=current_user["id"], comment=id)
    # Increment the number of likes on the post
    liked_comment.likes += 1
    
    db.add(new_like)
    db.commit()
    db.refresh(new_like)

    return new_like


@router.delete("/{id}/like", status_code=status.HTTP_204_NO_CONTENT)
def delete_like(id: int, db: Session = Depends(get_db),
        current_user: int = Depends(auth.get_current_user)):
    
    # The post where the like is being deleted
    comment = db.query(PostComment).filter(PostComment.id == id).first()

    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id: {id} does not exist")

    if comment.owner != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    like_query = db.query(CommentLike).filter(CommentLike.owner == current_user["id"],
        CommentLike.comment == id)
    like = like_query.first()
    
    # Check wether like object already exists
    if like is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"like on comment with id: {id} does not exist")
    
    # Delete the like and decrement the number of likes on the post
    like_query.delete(synchronize_session=False)
    comment.likes -= 1

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
