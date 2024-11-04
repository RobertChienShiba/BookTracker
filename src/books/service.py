
from sqlmodel import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Book
from .schemas import BookCreateModel, BookUpdateModel
from src.errors import BookNotFound


class BookService:
    async def get_all_books(self, session: AsyncSession):
        statement = select(Book).order_by(desc(Book.created_at))

        result = await session.execute(statement)

        return result.scalars().all()

    async def get_user_books(self, user_uid: str, session: AsyncSession):
        statement = (
            select(Book)
            .where(Book.user_uid == user_uid)
            .order_by(desc(Book.created_at))
        )

        result = await session.execute(statement)

        return result.scalars().all()

    async def get_book(self, book_uid: str, session: AsyncSession):
        statement = select(Book).where(Book.uid == book_uid)

        result = await session.execute(statement)

        book = result.scalars().first()  

        if book is None:
            raise BookNotFound()

        return book 

    async def create_book(
        self, book_data: BookCreateModel, user_uid: str, session: AsyncSession
    ):
        book_data_dict = book_data.model_dump()

        new_book = Book(**book_data_dict)

        new_book.user_uid = user_uid

        session.add(new_book)

        await session.commit()

        return new_book

    async def update_book(
        self, book_uid: str, update_data: BookUpdateModel, session: AsyncSession
    ):
        book_to_update = await self.get_book(book_uid, session)

        if book_to_update is not None:
            update_data_dict = update_data.model_dump()

            for k, v in update_data_dict.items():
                setattr(book_to_update, k, v)

            session.add(book_to_update)

            await session.commit()

            return book_to_update
        

    async def delete_book(self, book_uid: str, session: AsyncSession):
        book_to_delete = await self.get_book(book_uid, session)

        await session.delete(book_to_delete)

        await session.commit()

        return {}
