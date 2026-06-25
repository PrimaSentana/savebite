# app/routers/merchant_auth.py
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import cloudinary
from app.core.cloudinary import delete_merchant_banner, delete_merchant_logo, upload_banner_photo_merchant, upload_profile_photo_merchant
from app.core.deps import get_current_merchant
from app.crud.merchants import build_merchant_response, delete_merchant, update_merchant
from app.database import get_db
from app.models.merchants import Merchant
from app.schemas.merchants import MerchantResponceImage, MerchantResponse, MerchantUpdate
from app.schemas.user import UserResponse
from app.crud import merchants as crud_merchant
from app.crud import menu as crud_menu

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024

router = APIRouter(prefix="/merchant", tags=["Merchant"])

@router.get("/me", response_model=MerchantResponse)
async def get_my_profile(current_merchant: Merchant = Depends(get_current_merchant)):
    return build_merchant_response(current_merchant)

@router.get("/me/dashboard")
async def get_dashboard(current_merchant: Merchant = Depends(get_current_merchant)):
    return {
        "message": f"Welcome, {current_merchant.name}",
        "user_id": current_merchant.id,
        "email": current_merchant.email
    }

@router.put("/me", response_model=MerchantResponse)
async def update_merchant_profile(
    data: MerchantUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    updated = await update_merchant(db, current_merchant, data)
    return build_merchant_response(updated)

@router.post("/me/logo-upload", response_model=MerchantResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code = 400,
            detail="Format file tidak didukung. Gunakan JPG, PNG, atau WEBP"
        )
    
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Ukuran file maksimal 5MB"
        )
    
    photo_url = await upload_profile_photo_merchant(file_bytes, current_merchant.id)
    
    current_merchant.logo_url = photo_url
    await db.commit()
    await db.refresh(current_merchant)
    
    return build_merchant_response(current_merchant)

@router.post("/me/banner-upload", response_model=MerchantResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code = 400,
            detail="Format file tidak didukung. Gunakan JPG, PNG, atau WEBP"
        )
    
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Ukuran file maksimal 5MB"
        )
    
    photo_url = await upload_banner_photo_merchant(file_bytes, current_merchant.id)
    
    current_merchant.banner_url = photo_url
    await db.commit()
    await db.refresh(current_merchant)
    
    return build_merchant_response(current_merchant)

# Hapus logo
@router.delete("/me/logo", response_model=MerchantResponse)
async def remove_logo(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    if not current_merchant.logo_url:
        raise HTTPException(status_code=400, detail="Tidak ada logo merchant")

    await delete_merchant_logo(current_merchant.id)
    current_merchant.logo_url = None
    await db.commit()
    await db.refresh(current_merchant)

    return build_merchant_response(current_merchant)

# Hapus banner
@router.delete("/me/banner", response_model=MerchantResponse)
async def remove_banner(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    if not current_merchant.banner_url:
        raise HTTPException(status_code=400, detail="Tidak ada banner merchant")

    await delete_merchant_banner(current_merchant.id)
    current_merchant.banner_url = None
    await db.commit()
    await db.refresh(current_merchant)

    return build_merchant_response(current_merchant)

@router.delete("/me")
async def delete_merchant_account(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menus = await crud_menu.get_menus_by_merchant(db, current_merchant.id)
    for menu in menus:
        if menu.image_url:
            await cloudinary.delete_menu_image(menu.id)
    if current_merchant.logo_url:
        await cloudinary.delete_merchant_logo(current_merchant.id)
    if current_merchant.banner_url:
        await cloudinary.delete_merchant_banner(current_merchant.id)
    
    await delete_merchant(db, current_merchant)
    
    return {
        "message": "Merchant account permanently deleted"
    }