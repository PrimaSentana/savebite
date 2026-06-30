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
from app.schemas.menu import BulkDeleteMenu, MenuCreate, MenuUpdate, MenuResponse, StockUpdate
from app.core.cloudinary import delete_menu_image, upload_menu_image
from app.crud import menu as crud_menu

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

