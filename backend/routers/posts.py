from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from starlette import status 

import aiofiles

import database
import models
from database import sessionLocal 
from models import User, Post, PostComment, PostLike

import schemas
from routers import auth

import string
import random
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
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db),
        current_user: schemas.CreateUserRequest = Depends(auth.get_current_user)):

    new_post = Post(owner_id=current_user["id"], **post.dict())

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user), 
        limit: int = 10, skip: int = 0, search: Optional[str] = ""):

    posts = db.query(Post, func.count(PostComment.post).label("post_comments")).join(
        PostComment, PostComment.post == Post.id, isouter=True).group_by(Post.id).filter(
            Post.content.contains(search)).limit(limit).offset(skip).all()
    
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
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db),
        current_user: int = Depends(auth.get_current_user)):

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
def delete_post(id: int, db: Session = Depends(get_db),
        current_user: int = Depends(auth.get_current_user)):

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


@router.post("/{id}/like", status_code=status.HTTP_201_CREATED, response_model=schemas.PostLike)
def create_like(id: int, db: Session = Depends(get_db),
        current_user: schemas.CreateUserRequest = Depends(auth.get_current_user)):
    # The post that being liked
    liked_post = db.query(Post).filter(Post.id == id).first()

    if liked_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    
    # Check wether like object already exists
    like_query = db.query(PostLike).group_by(PostLike.id).filter(
        PostLike.owner == current_user["id"], PostLike.post == id).first()

    if like_query is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You cannot like one post twice")

    # Create like object
    new_like = PostLike(owner=current_user["id"], post=id)
    # Increment the number of likes on the post
    liked_post.likes += 1
    
    db.add(new_like)
    db.commit()
    db.refresh(new_like)

    return new_like


@router.delete("/{id}/like", status_code=status.HTTP_204_NO_CONTENT)
def delete_like(id: int, db: Session = Depends(get_db),
        current_user: int = Depends(auth.get_current_user)):
    
    # The post where the like is being deleted
    post = db.query(Post).filter(Post.id == id).first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    if post.owner_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    like_query = db.query(PostLike).filter(PostLike.owner == current_user["id"], PostLike.post == id)
    like = like_query.first()
    
    # Check wether like object already exists
    if like is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"like on post with id: {id} does not exist")
    
    # Delete the like and decrement the number of likes on the post
    like_query.delete(synchronize_session=False)
    post.likes -= 1

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/{id}/upload-image')
async def upload_image(id: int, db: Session = Depends(get_db), image: UploadFile = File(...),
        current_user: int = Depends(auth.get_current_user)):
    
    post = db.query(Post).filter(Post.id == id).first()

    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} does not exist")
    
    content = image.read()

    letters = string.ascii_letters

    rand_str = ''.join(random.choice(letters) for i in range(8))
    new = f'_{rand_str}.'

    filename = new.join(image.filename.rsplit('.', 1))
    
    async with aiofiles.open(os.path.join('app/static/images', filename), mode='wb') as f:
        await f.write(content)
        
    post.image_1 = filename    

    return {'filename': post.image_1}
