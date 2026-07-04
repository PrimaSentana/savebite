# app/routers/menu.py
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.models.menu import MenuCategory, MenuStatus
from app.models.merchants import Merchant
from app.core.deps import get_current_merchant
from app.schemas.menu import BulkDeleteMenu, MenuCreate, MenuUpdate, MenuResponse, PeriodUpdate, StockUpdate
from app.core.cloudinary import delete_menu_image, upload_menu_image
from app.crud import menu as crud_menu

router = APIRouter(prefix="/merchant/menus", tags=["Merchant Menus"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024  # 5MB

# Get all menu
@router.get("/all", response_model=List[MenuResponse])
async def get_all_menu(
    db: AsyncSession = Depends(get_db)
):
    return await crud_menu.get_all_menu(db)

@router.get("/", response_model=List[MenuResponse])
async def get_my_menus(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    return await crud_menu.get_menus_by_merchant(db, current_merchant.id)

@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu_by_id(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await crud_menu.get_menu_by_id(db, menu_id)

# Create menu baru
@router.post("/", response_model=MenuResponse, status_code=201)
async def create_menu(
    title: str = Form(...),
    category: MenuCategory = Form(...),
    original_price: Decimal = Form(...),
    discounted_price: Decimal = Form(...),
    quantity: int = Form(...),
    description: Optional[str] = Form(None),
    max_order_per_user: Optional[int] = Form(None),
    available_from: Optional[datetime] = Form(None),
    available_until: Optional[datetime] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    if discounted_price >= original_price:
        raise HTTPException(
            status_code=400,
            detail="Discounted price must be lower than original price"
        )
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    
    data = MenuCreate(
        title=title,
        description=description,
        category=category,
        original_price=original_price,
        discounted_price=discounted_price,
        quantity=quantity,
        max_order_per_user=max_order_per_user,
        available_from=available_from,
        available_until=available_until
    )
    
    menu = await crud_menu.create_menu(db, current_merchant.id, data)
    
    if image is not None:
        # if image.content_type not in ALLOWED_TYPES:
        #     raise HTTPException(
        #         status_code=400,
        #         detail="File format not supported. Use JPG, PNG, or WEBP"
        #     )
        file_bytes = await image.read()
        if len(file_bytes) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File size max 5MB")
        image_url = await upload_menu_image(file_bytes, menu.id)
        menu.image_url = image_url
        await db.commit()
        await db.refresh(menu)
    return menu

# Update menu
@router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int,
    data: MenuUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menu = await crud_menu.get_menu_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    if menu.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="You don't own this menu")

    return await crud_menu.update_menu(db, menu, data)

@router.patch("/{menu_id}/stock", response_model=MenuResponse)
async def edit_menu_stock(
    menu_id: int,
    data: StockUpdate,
    db: AsyncSession = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    menu = await crud_menu.get_menu_by_id(db, menu_id)
    if not menu:
        raise HTTPException(
            status_code=404,
            detail="Menu not found"
        )
    if menu.merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=403,
            detail="You dont own this menu"
        )

    menu.quantity = data.quantity
    menu.max_order_per_user = data.quantity
    
    if menu.quantity == 0:
        menu.status = MenuStatus.SOLD_OUT
    elif menu.status == MenuStatus.SOLD_OUT and data.quantity:
        menu.status = MenuStatus.ON_SALE
        
    await db.commit()
    await db.refresh(menu)
    return menu

@router.patch("/{menu_id}/period", response_model=MenuResponse)
async def update_period(
    menu_id: int,
    data: PeriodUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menu = await crud_menu.get_menu_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan")
    if menu.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="Akses ditolak. Anda bukan pemilik menu ini")
    
    menu.available_from = data.available_from
    menu.available_until = data.available_until
    
    if data.available_until is None and not menu.is_active:
        menu.is_active = True
        menu.status = MenuStatus.ON_SALE
    
    await db.commit()
    await db.refresh(menu)
    return menu

# Upload menu image
@router.post("/{menu_id}/image", response_model=MenuResponse)
async def upload_image(
    menu_id: int,
    file: UploadFile = File(...),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menu = await crud_menu.get_menu_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    if menu.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="You don't own this menu")
    # if file.content_type not in ALLOWED_TYPES:
    #     raise HTTPException(status_code=400, detail="File format not supported")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File size max 5MB")

    image_url = await upload_menu_image(file_bytes, menu_id)
    menu.image_url = image_url
    await db.commit()
    await db.refresh(menu)

    return menu

# Activated Menu
@router.put("/activate/{menu_id}")
async def activate_menu(
    menu_id: int,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menu = await crud_menu.get_menu_by_id_deactive(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    if menu.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="You don't own this menu")

    await crud_menu.activated_menu(db, menu)
    return {
        "message": "Menu active successfully",
        "data": menu
    }

# Delete menu (soft delete)
@router.delete("/deactivate/{menu_id}")
async def deactivate_menu(
    menu_id: int,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menu = await crud_menu.get_menu_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    if menu.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="You don't own this menu")

    await crud_menu.deactive_menu(db, menu)
    return {
        "message": "Menu deleted successfully"
    }

#bulk delete
@router.delete("/bulk-delete")
async def bulk_delete_menu(
    data: BulkDeleteMenu,
    db: AsyncSession = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    deleted_count = await crud_menu.bulk_delete_menu(
        db, 
        current_merchant.id, 
        data.menu_ids
    )
    
    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="No menus found or you don't own these menus"
        )
    
    return {
        "message": f"{deleted_count} menu(s) deleted successfully",
        "deleted_count": deleted_count
    }

@router.delete("/{menu_id}/permanent-delete")
async def permanent_delete_menu(
    menu_id: int,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    menu = await crud_menu.get_menu_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    if menu.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="You don't own this menu")

    if menu.image_url:
        await delete_menu_image(menu.id)
    
    await crud_menu.delete_menu(db, menu)
    return {
        "message": "Menu permanently deleted"
    }
    