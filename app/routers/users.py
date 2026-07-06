from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloudinary import delete_profile_photo, upload_profile_photo
from app.database import get_db
from app.models.user import User
from app.schemas.user import ChangeEmail, ChangePassword, UpdateUsername, UserResponse
from app.crud import user as crud_user
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
    
@router.put("/me/username", response_model=UserResponse)
async def update_my_username(
    data: UpdateUsername,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if username already taken
    existing = await crud_user.get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    return await crud_user.update_username(db, current_user, data.username)

@router.put("/me/email", response_model=ChangeEmail)
async def update_email(
    data: ChangeEmail,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    existing = await crud_user.get_user_by_email(db, data.new_email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already in use"
        )
    
    user = await crud_user.change_user_email(db, current_user, data.new_email)
    return user
    
@router.put("/me/password")
async def update_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await crud_user.change_user_password(
        db,
        current_user,
        data.current_password,
        data.new_password
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    return {
        "message: Password updated successfully"
    }

@router.post("/me/photo-test")
async def upload_photo(
    file: UploadFile = File(...),
):
    mime = file.content_type
    print(mime)
    
    return {
        "filename": file.filename,
        "file_type": mime
    }

@router.post("/me/photo", response_model=UserResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # mime = file.content_type
    # print(mime)
    # if file.content_type not in ALLOWED_TYPES:
    #     raise HTTPException(
    #         status_code = 400,
    #         detail="Format file tidak didukung. Gunakan JPG, PNG, atau WEBP"
    #     )
    
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

@router.delete("/me")
async def delete_my_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.image:
        await delete_profile_photo(current_user.id)
        
    await crud_user.delete_user(db, current_user)
    return{
        "message": "Account permanently deleted"
    }