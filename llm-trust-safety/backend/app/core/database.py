"""
Database setup - SQLAlchemy async com SQLite
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from app.models import db_models
        await conn.run_sync(Base.metadata.create_all)

        # Migrações idempotentes para bancos existentes (SQLite-friendly)
        # Adicionar coluna source_type se ela ainda não existir.
        from sqlalchemy import text
        for table in ("evaluation_logs", "sessions"):
            try:
                cols = await conn.execute(text(f"PRAGMA table_info({table})"))
                col_names = [row[1] for row in cols.fetchall()]
                if "source_type" not in col_names:
                    await conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN source_type VARCHAR(30) DEFAULT 'live'"
                    ))
            except Exception:
                # Não-SQLite ou tabela ainda não criada: ignorar silenciosamente
                pass
