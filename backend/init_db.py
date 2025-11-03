import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.hash import pbkdf2_sha256 as bcrypt
from database import Base, settings
from models import User, UserRole

async def init_users():
    # Используем переменную окружения для URL базы данных
    from database import settings
    
    print(f"[init_db] Starting database initialization...")
    print(f"[init_db] Database URL: {settings.database_url}")
    
    # Создаем директорию для БД, если её нет (только если путь абсолютный)
    db_path = settings.database_url.replace('sqlite+aiosqlite:///', '')
    print(f"[init_db] Database path: {db_path}")
    
    if db_path.startswith('/'):
        # Абсолютный путь
        db_dir = os.path.dirname(db_path)
        print(f"[init_db] Database directory: {db_dir}")
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print(f"[init_db] Created directory: {db_dir}")
            except OSError as e:
                # Если не можем создать (например, диск еще не смонтирован), пропускаем
                # Директория будет создана автоматически при монтировании диска
                print(f"[init_db] Warning: Could not create directory {db_dir}: {e}")
    
    try:
        engine = create_async_engine(settings.database_url)
        print(f"[init_db] Engine created")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print(f"[init_db] Tables created")

        AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

        async with AsyncSessionLocal() as session:
            # Create default users
            users_data = [
                {"username": "admin1", "password": "nimda", "role": UserRole.admin},
                {"username": "admin2", "password": "nimda", "role": UserRole.admin},
                {"username": "logist", "password": "logist", "role": UserRole.logist},
                {"username": "work", "password": "work", "role": UserRole.work},
            ]

            created_count = 0
            updated_count = 0
            for user_data in users_data:
                # Check if user already exists
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()

                if not existing_user:
                    # Create new user
                    hashed = bcrypt.hash(user_data["password"][:72])  # bcrypt limit
                    user = User(
                        username=user_data["username"],
                        hashed_password=hashed,
                        role=user_data["role"]
                    )
                    session.add(user)
                    created_count += 1
                    print(f"[init_db] Created user: {user_data['username']} (role: {user_data['role'].value})")
                else:
                    # Update existing user password to ensure it's correctly hashed
                    # This fixes potential issues with old password hashes
                    hashed = bcrypt.hash(user_data["password"][:72])
                    existing_user.hashed_password = hashed
                    existing_user.is_active = True  # Ensure user is active
                    if existing_user.role != user_data["role"]:
                        existing_user.role = user_data["role"]
                    updated_count += 1
                    print(f"[init_db] Updated user: {user_data['username']} (role: {user_data['role'].value}, password reset)")

            await session.commit()
            print(f"[init_db] Database initialized: {created_count} new users created, {updated_count} users updated, {len(users_data)} total users")
    except Exception as e:
        print(f"[init_db] ERROR during initialization: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(init_users())