import logging

from fastapi import status
from fastapi.exceptions import HTTPException
from sqlmodel import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_

from src.auth.service import UserService
from src.books.service import BookService
from src.db.models import Review
from src.errors import ReviewNotFound, BookNotFound, UserNotFound, ReviewExists

from .schemas import ReviewCreateModel

book_service = BookService()
user_service = UserService()


class ReviewService:
    async def add_review_to_book(
        self,
        user_email: str,
        book_uid: str,
        review_data: ReviewCreateModel,
        session: AsyncSession,
    ):
        book = await book_service.get_book(book_uid=book_uid, session=session)
        user = await user_service.get_user_by_email(
            email=user_email, session=session
        )

        statement = select(Review).where(and_(Review.user_uid == user.uid, Review.book_uid == book.uid))
        duplicate = await session.execute(statement)
        duplicate = duplicate.scalar_one_or_none()
        
        if duplicate is not None:
            raise ReviewExists

        review_data_dict = review_data.model_dump()

        if not book:
            raise BookNotFound
        
        if not user:
            raise UserNotFound

        new_review = Review(**review_data_dict, user=user, book=book)

        session.add(new_review)

        await session.commit()

        return new_review
    

    async def get_review(self, review_uid: str, session: AsyncSession):
        statement = select(Review).where(Review.uid == review_uid)

        result = await session.execute(statement)

        review = result.scalars().first()  

        if review is None:
            raise ReviewNotFound()
        
        return review


    async def get_all_reviews(self, session: AsyncSession):
        statement = select(Review).order_by(desc(Review.created_at))

        result = await session.execute(statement)

        return result.scalars().all()


    async def delete_review_to_from_book(
        self, review_uid: str, user_email: str, session: AsyncSession
    ):
        user = await user_service.get_user_by_email(user_email, session)

        review = await self.get_review(review_uid, session)

        if not review or (review.user != user):
            raise HTTPException(
                detail="Cannot delete this review",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        await session.delete(review)

        await session.commit()
