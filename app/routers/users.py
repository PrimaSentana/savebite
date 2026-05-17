from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloudinary import delete_profile_photo, upload_profile_photo
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.deps import get_current_user

router = APIRouter(prefix="/users", tags=['Users'])

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/me/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Welcome, {current_user.username}",
        "user_id": current_user.id,
        "email": current_user.email
    }

@router.post("/me/photo", response_model=UserResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
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
    
    photo_url = await upload_profile_photo(file_bytes, current_user.id)
    
    current_user.image = photo_url
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

@router.delete("/me/photo", response_model=UserResponse)
async def delete_photo(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.image:
        raise HTTPException(status_code=400, detail="Tidak ada foto profile")

    await delete_profile_photo(current_user.id)
    
    current_user.image = None
    await db.commit()
    await db.refresh(current_user)
    
    return current_user