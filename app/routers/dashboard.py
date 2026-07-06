# app/routers/menu.py
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.menu import MenuCategory, MenuStatus
from app.models.merchants import Merchant
from app.core.deps import get_current_merchant
from app.schemas.menu import BulkDeleteMenu, MenuCreate, MenuUpdate, MenuResponse, StockUpdate
from app.core.cloudinary import delete_menu_image, upload_menu_image
from app.crud import menu as crud_menu, merchants as crud_merchants
from app.schemas.merchants import MerchantDetailResponse, MerchantResponse


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
        .options(selectinload(Merchant.menus))
    )
    merchant = result.scalar_one_or_none()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant tidak ditemukan")
    
    active_menus = [
        menu for menu in merchant.menus
        if menu.is_active and menu.status == MenuStatus.ON_SALE and menu.quantity > 0
    ]
    
    location = crud_merchants.extract_location(merchant)
    
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
        menus = active_menus
    )