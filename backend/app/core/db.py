from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Session, create_engine, select, SQLModel

from app.core.config import settings
from app.models import User, Role
from app.schemas.user import UserCreate
from app import crud

sync_engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace(
        "postgresql+psycopg", "postgresql+psycopg2"
    ),
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_session() -> Session:
    with Session(sync_engine) as session:
        yield session


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    
    if not user:
        admin_role = session.exec(
            select(Role).where(Role.role_name == "admin")
        ).first()
        
        if not admin_role:
            admin_role = Role(
                role_name="admin",
                description="Administrator with full access"
            )
            session.add(admin_role)
            session.commit()
            session.refresh(admin_role)
        
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            first_name="Super",
            last_name="Admin",
            is_active=True,
            is_email_verified=True,
        )
        user = crud.create_user(session=session, user_create=user_in, role_id=admin_role.role_id)
        print(f"Superuser created: {user.email}")
    else:
        print(f"Superuser already exists: {user.email}")


async def create_db_and_tables() -> None:
    async with async_engine.begin() as conn:
        from app import models
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    await async_engine.dispose()