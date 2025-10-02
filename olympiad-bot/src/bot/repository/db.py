"""Database configuration using SQLAlchemy."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
