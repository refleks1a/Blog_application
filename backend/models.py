from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text

from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import FileType

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(63), unique=True)
    first_name = Column(String(63))
    last_name = Column(String(63))
    hashed_password = Column(String(127))


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    owner = relationship("User")

    content = Column(String(255), nullable = True)
    likes = Column(Integer, server_default = text("0"), nullable = False)
    reposts = Column(Integer, server_default = text("0"), nullable = False)
    saves = Column(Integer, server_default = text("0"), nullable = False)
    comments = relationship("PostComment", backref = "post_comment")

    image_1 = Column(FileType(storage=FileSystemStorage(path="/static/images"), length=63), 
                     nullable = True)
    
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    

class Comment():
    id = Column(Integer, primary_key=True, index=True)
    
    post = Column(Integer, ForeignKey("posts.id"), nullable = False)
    owner = Column(Integer, ForeignKey("users.id"), nullable = False)

    content = Column(String(255), nullable = False)
    likes = Column(Integer, server_default = text("0"), nullable = False)

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    author_like = Column(Boolean, server_default = text("FALSE"), nullable = False)


class PostComment(Base, Comment):
    __tablename__ = "post_comments"


class CommentOnComment(Base, Comment):
    __tablename__ = "comment_comments"
    
    comment = Column(Integer, ForeignKey("post_comments.id"), nullable = False)


class Like():
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(Integer, ForeignKey("users.id"), nullable = False)

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class PostLike(Base, Like):
    __tablename__ = "post_likes"

    post = Column(Integer, ForeignKey("posts.id"), nullable = False)


class CommentLike(Base, Like):
    __tablename__ = "comment_likes"
    
    comment = Column(Integer, ForeignKey("post_comments.id"), nullable = False)
