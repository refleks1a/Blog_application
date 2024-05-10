from sqlalchemy import Boolean, Column, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(63), unique=True)
    first_name = Column(String(63))
    last_name = Column(String(63))
    hashed_password = Column(String(127))