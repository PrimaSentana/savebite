from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.deps import get_current_user


router = APIRouter(prefix="/users", tags=['Users'])

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

