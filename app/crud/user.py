from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserCreate):
    hashed = hash_password(user_data.password)
    new_user = User(
        email = user_data.email,
        username = user_data.username,
        password = hashed
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

async def update_username(db: AsyncSession, user: User, username: str):
    user.username = username
    await db.commit()
    await db.refresh(user)
    return user

async def change_user_email(db: AsyncSession, user: User, new_email: str):
    user.email = new_email
    await db.commit()
    await db.refresh(user)
    return user

async def change_user_password(db:AsyncSession, user: User, current_password: str, new_password: str):
    if not verify_password(current_password, user.password):
        return None

    user.password = hash_password(new_password)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db:AsyncSession, user: User):
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user

async def activated_user(db:AsyncSession, user: User):
    user.is_active = True
    await db.commit()