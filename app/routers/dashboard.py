# app/routers/menu.py
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.crud.review import get_reviews_by_merchant
from app.crud.transaction import get_user_transactions
from app.database import get_db
from app.models.menu import Menu, MenuCategory, MenuStatus
from app.models.merchants import Merchant
from app.core.deps import get_current_user
from app.models.review import Review
from app.models.transaction import Order, TransactionStatus
from app.models.transaction_item import TransactionItem
from app.models.user import User
from app.schemas.menu import BulkDeleteMenu, MenuCreate, MenuUpdate, MenuResponse, StockUpdate
from app.core.cloudinary import delete_menu_image, upload_menu_image
from app.crud import menu as crud_menu, merchants as crud_merchants
from app.schemas.merchants import MerchantDetailResponse, MerchantResponse
from app.schemas.review import ReviewMenuResponse, ReviewResponse
from app.schemas.transaction import UserTransactionResponse


router = APIRouter(prefix="/dashboard", tags=["Users Dashboard"])

#get all menus
@router.get("/all", response_model=List[MenuResponse])
async def get_all_menu(
    db: AsyncSession = Depends(get_db)
):
    return await crud_menu.get_all_menu(db)

#get menu by id
@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu_by_id(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await crud_menu.get_menu_by_id(db, menu_id)

#get menu (>=50%)
@router.get("/menu/hemat", response_model=List[MenuResponse])
async def get_menu_hemat(
    db: AsyncSession = Depends(get_db)
):
    return await crud_menu.get_menu_hemat(db)

#inspect merchant detail
@router.get("/merchant/{merchant_id}", response_model=MerchantDetailResponse)
async def get_merchant_detail(
    merchant_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Merchant)
        .where(
            Merchant.id == merchant_id,
            Merchant.is_active == True
        )
        .options(
            selectinload(Merchant.menus),
            selectinload(Merchant.reviews).selectinload(Review.user),
            selectinload(Merchant.reviews).selectinload(Review.transaction).selectinload(Order.items).selectinload(TransactionItem.menu)
            
        )
    )
    merchant = result.scalar_one_or_none()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant tidak ditemukan")
    
    active_menus = [
        menu for menu in merchant.menus
        if menu.is_active and menu.status == MenuStatus.ON_SALE and menu.quantity > 0
    ]
    
    location = crud_merchants.extract_location(merchant)
    
    reviews = []
    for review in merchant.reviews:
        ordered_menus = []
        if review.transaction and review.transaction.items:
            for item in review.transaction.items:
                if item.menu:
                    ordered_menus.append(ReviewMenuResponse(
                        id = item.menu.id,
                        title = item.menu_title,
                        image_url = item.menu.image_url,
                        discounted_price = float(item.menu_price),
                        quantity = item.quantity
                    ))
        reviews.append({
            "id": review.id,
            "user_id": review.user_id,
            "merchant_id": review.merchant_id,
            "transaction_id": review.transaction_id,
            "rating": review.rating,
            "comment": review.comment,
            "photo_url": review.photo_url,
            "merchant_reply": review.merchant_reply,
            "replied_at": review.replied_at,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "reviewer_username": review.user.username if review.user else None,
            "ordered_menus": ordered_menus,
        })
    
    return MerchantDetailResponse(
        id = merchant.id,
        name = merchant.name,
        description = merchant.description,
        email = merchant.email,
        phone = merchant.phone,
        logo_url = merchant.logo_url,
        banner_url = merchant.banner_url,
        address = merchant.address,
        latitude = location["latitude"],
        longitude = location["longitude"],
        is_active = merchant.is_active,
        is_open = merchant.is_open,
        menus = active_menus,
        reviews = reviews
    )
    
# get user transaction
@router.get("/user/activity", response_model=List[UserTransactionResponse])
async def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_user_transactions(db, current_user.id)
    return result

@router.get("/menu/best-seller", response_model=List[MenuResponse])
async def get_best_seller_menus(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(
            Menu,
            func.sum(TransactionItem.quantity).label("total_sold"),
        )
        .join(TransactionItem, Menu.id == TransactionItem.menu_id)
        .join(Order, TransactionItem.transaction_id == Order.id)
        .where(
            Order.status == TransactionStatus.PAID or Order.status == TransactionStatus.COMPLETED,
            Menu.quantity > 0,
            Menu.is_active == True
        )
        .group_by(Menu.id)
        .order_by(func.sum(TransactionItem.quantity).desc())
        .limit(3)
    )
    rows = result.all()
    top_menus = []
    
    for menu_obj, total_sold in rows:
        menu_obj.total_sold = int(total_sold)
        top_menus.append(menu_obj)
            
    return top_menus