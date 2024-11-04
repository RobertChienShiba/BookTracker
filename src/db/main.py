from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel
from typing import AsyncGenerator

from src.config import Config

async_engine = create_async_engine(url=Config.DATABASE_URL, echo=True)


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    Session = async_sessionmaker(
        async_engine, expire_on_commit=False
    )

    async with Session() as session:
        yield session