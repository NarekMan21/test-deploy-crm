import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.hash import pbkdf2_sha256 as bcrypt
from database import Base, settings
from models import User, UserRole

async def init_users():
    # Используем переменную окружения для URL базы данных
    import os
    from database import settings
    
    # Создаем директорию для БД, если её нет
    db_path = settings.database_url.replace('sqlite+aiosqlite:///', '')
    if db_path.startswith('/'):
        # Абсолютный путь
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Create default users
        users_data = [
            {"username": "admin1", "password": "nimda", "role": UserRole.admin},
            {"username": "admin2", "password": "nimda", "role": UserRole.admin},
            {"username": "logist", "password": "logist", "role": UserRole.logist},
            {"username": "work", "password": "work", "role": UserRole.work},
        ]

        for user_data in users_data:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.username == user_data["username"])
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                user = User(
                    username=user_data["username"],
                    hashed_password=bcrypt.hash(user_data["password"][:72]),  # bcrypt limit
                    role=user_data["role"]
                )
                session.add(user)
                print(f"Created user: {user_data['username']}")

        await session.commit()
        print("Database initialized with default users")

if __name__ == "__main__":
    asyncio.run(init_users())