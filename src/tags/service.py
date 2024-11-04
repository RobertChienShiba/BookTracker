from fastapi import status
from fastapi.exceptions import HTTPException
from sqlmodel import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.books.service import BookService
from src.db.models import Tag

from .schemas import TagAddModel, TagCreateModel
from src.errors import BookNotFound, TagNotFound, TagAlreadyExists

book_service = BookService()


server_error = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong"
)


class TagService:

    async def get_tags(self, session: AsyncSession):
        """Get all tags"""

        statement = select(Tag).order_by(desc(Tag.created_at))

        result = await session.execute(statement)

        return result.scalars().all()

    async def add_tags_to_book(
        self, book_uid: str, tag_data: TagAddModel, session: AsyncSession
    ):
        """Add tags to a book"""

        book = await book_service.get_book(book_uid=book_uid, session=session)

        if not book:
            raise BookNotFound()

        for tag_item in tag_data.tags:
            result = await session.execute(select(Tag).where(Tag.name == tag_item.name))

            tag = result.scalars().one_or_none()
            if not tag:
                tag = Tag(name=tag_item.name)

            book.tags.append(tag)

        session.add(book)

        await session.commit()

        await session.refresh(book)

        return book

    async def get_tag_by_uid(self, tag_uid: str, session: AsyncSession):
        """Get tag by uid"""

        statement = select(Tag).where(Tag.uid == tag_uid)

        result = await session.execute(statement)

        return result.scalars().first()  

    async def add_tag(self, tag_data: TagCreateModel, session: AsyncSession):
        """Create a tag"""

        statement = select(Tag).where(Tag.name == tag_data.name)

        result = await session.execute(statement)

        tag = result.scalars().first()  

        if tag:
            raise TagAlreadyExists()
        new_tag = Tag(name=tag_data.name)

        session.add(new_tag)

        await session.commit()

        return new_tag

    async def update_tag(
        self, tag_uid, tag_update_data: TagCreateModel, session: AsyncSession
    ):
        """Update a tag"""

        tag = await self.get_tag_by_uid(tag_uid, session)

        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        update_data_dict = tag_update_data.model_dump()

        for k, v in update_data_dict.items():
            setattr(tag, k, v)
        
        session.add(tag)

        await session.commit()

        return tag

    async def delete_tag(self, tag_uid: str, session: AsyncSession):
        """Delete a tag"""

        tag = await self.get_tag_by_uid(tag_uid,session)

        if not tag:
            raise TagNotFound()

        await session.delete(tag)

        await session.commit()