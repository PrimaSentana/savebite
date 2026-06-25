from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.crud.merchants import authenticate_merchant, build_merchant_response, create_merchant, get_merchant_by_email
from app.database import get_db
from app.models.user import User
from app.schemas.merchants import MerchantCreate, MerchantLogin, MerchantResponse
from app.schemas.user import RefreshTokenRequest, TokenResponse, UserLogin, UserResponse, UserCreate
from app.crud import user as crud_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register-user", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_email = await crud_user.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar"
        )

    existing_username = await crud_user.get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah dipakai"
        )

    new_user = await crud_user.create_user(db, user_data)
    return new_user

@router.post("/login-user", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await crud_user.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif"
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": "user"})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "role": "user"})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = verify_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau sudah expired"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid"
        )
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        await HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan atau tidak aktif"
        )
    
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token = new_access_token,
        refresh_token = new_refresh_token
    )
    
@router.post("/register-merchant", response_model=MerchantResponse, status_code=201)
async def register_merchant(data: MerchantCreate, db: AsyncSession = Depends(get_db)):
    # Cek email sudah terdaftar
    existing = await get_merchant_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    merchant = await create_merchant(db, data)
    return build_merchant_response(merchant)

@router.post("/login-merchant", response_model=TokenResponse)
async def login_merchant(data: MerchantLogin, db: AsyncSession = Depends(get_db)):
    merchant = await authenticate_merchant(db, data.email, data.password)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah"
        )

    if not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun merchant tidak aktif"
        )

    access_token = create_access_token(data={"sub": str(merchant.id), "role": "merchant"})
    refresh_token = create_refresh_token(data={"sub": str(merchant.id), "role": "merchant"})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )