import uuid
from datetime import date, datetime
from typing import List, Optional

import sqlalchemy.dialects.sqlite as sqlite
from sqlmodel import Column, Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: str = Field(
        sa_column=Column(
            sqlite.CHAR(36),
            primary_key=True,
            unique=True,
            index=True,
            nullable=False,
            default=lambda: str(uuid.uuid4())  
        )
    )
    username: str
    email: str
    first_name: str
    last_name: str
    role: str = Field(
        sa_column=Column(sqlite.VARCHAR, nullable=False, server_default="user")
    )
    is_verified: bool = Field(default=False)
    password_hash: str = Field(
        sa_column=Column(sqlite.VARCHAR, nullable=False), exclude=True
    )
    created_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    update_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    books: List["Book"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    reviews: List["Review"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self):
        return f"<User {self.username}>"


class BookTag(SQLModel, table=True):
    book_id: str = Field(default=None, foreign_key="books.uid", primary_key=True)
    tag_id: str = Field(default=None, foreign_key="tags.uid", primary_key=True)

class Tag(SQLModel, table=True):
    __tablename__ = "tags"
    uid: str = Field(
        sa_column=Column(
            sqlite.CHAR(36), 
            primary_key=True,
            unique=True,
            index=True,
            nullable=False,
            default=lambda: str(uuid.uuid4())  
        )
    )
    name: str = Field(sa_column=Column(sqlite.VARCHAR, nullable=False))
    created_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    books: List["Book"] = Relationship(
        link_model=BookTag,
        back_populates="tags",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class Book(SQLModel, table=True):
    __tablename__ = "books"
    uid: str = Field(
        sa_column=Column(
            sqlite.CHAR(36), 
            primary_key=True,
            unique=True,
            index=True,
            nullable=False,
            default=lambda: str(uuid.uuid4())  
        )
    )
    title: str
    author: str
    publisher: str
    published_date: date
    page_count: int
    language: str
    user_uid: Optional[str] = Field(default=None, foreign_key="users.uid")
    created_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    update_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    user: Optional[User] = Relationship(back_populates="books")
    reviews: List["Review"] = Relationship(
        back_populates="book", sa_relationship_kwargs={"lazy": "selectin"}
    )
    tags: List[Tag] = Relationship(
        link_model=BookTag,
        back_populates="books",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __repr__(self):
        return f"<Book {self.title}>"


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    uid: str = Field(
        sa_column=Column(
            sqlite.CHAR(36), 
            primary_key=True,
            unique=True,
            index=True,
            nullable=False,
            default=lambda: str(uuid.uuid4())  
        )
    )
    rating: int = Field(lt=5)
    review_text: str = Field(sa_column=Column(sqlite.VARCHAR, nullable=False))
    user_uid: Optional[str] = Field(default=None, foreign_key="users.uid")
    book_uid: Optional[str] = Field(default=None, foreign_key="books.uid")
    created_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    update_at: datetime = Field(sa_column=Column(sqlite.TIMESTAMP, default=datetime.now))
    user: Optional[User] = Relationship(back_populates="reviews")
    book: Optional[Book] = Relationship(back_populates="reviews")

    def __repr__(self):
        return f"<Review for book {self.book_uid} by user {self.user_uid}>"
    