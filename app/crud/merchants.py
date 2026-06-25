# app/crud/merchant.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from app.models.merchants import Merchant
from app.schemas.merchants import MerchantCreate, MerchantUpdate
from app.core.security import hash_password, verify_password

async def get_merchant_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(Merchant).where(Merchant.email == email))
    return result.scalar_one_or_none()

async def get_merchant_by_id(db: AsyncSession, merchant_id: int):
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    return result.scalar_one_or_none()

async def create_merchant(db: AsyncSession, data: MerchantCreate):
    merchant = Merchant(
        email=data.email,
        password=hash_password(data.password),
        name=data.name,
        phone=data.phone,
        address=data.address,
        description=data.description,
        location=from_shape(Point(data.longitude, data.latitude), srid=4326)
    )
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)
    return merchant

async def authenticate_merchant(db: AsyncSession, email: str, password: str):
    merchant = await get_merchant_by_email(db, email)
    if not merchant:
        return None
    if not verify_password(password, merchant.password):
        return None
    return merchant

async def update_merchant(db: AsyncSession, merchant: Merchant, data: MerchantUpdate):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(merchant, field, value)
    await db.commit()
    await db.refresh(merchant)
    return merchant

def extract_location(merchant: Merchant) -> dict:
    if merchant.location is None:
        return {"latitude": None, "longitude": None}
    shape = to_shape(merchant.location)
    return {"latitude": shape.y, "longitude": shape.x}

def build_merchant_response(merchant: Merchant) -> dict:
    location = extract_location(merchant)
    return {
        "id": merchant.id,
        "email": merchant.email,
        "name": merchant.name,
        "phone": merchant.phone,
        "address": merchant.address,
        "description": merchant.description,
        "logo_url": merchant.logo_url,
        "banner_url": merchant.banner_url,
        "is_active": merchant.is_active,
        "is_open": merchant.is_open,
        "latitude": location["latitude"],
        "longitude": location["longitude"],
    }
    
async def delete_merchant(db: AsyncSession, merchant: Merchant):
    await db.delete(merchant) 
    await db.commit() 