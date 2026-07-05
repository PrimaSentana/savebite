# app/routers/merchant_transaction.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_db
from app.models.merchants import Merchant
from app.models.transaction import Order, TransactionStatus
from app.core.deps import get_current_merchant
from app.schemas.transaction import TransactionResponse
from app.crud.transaction import update_transaction_status

router = APIRouter(prefix="/merchant/orders", tags=["Merchant Orders"])

# Get all incoming orders
@router.get("/", response_model=List[TransactionResponse])
async def get_all_orders(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .where(Order.merchant_id == current_merchant.id)
        .options(
            selectinload(Order.items),
            selectinload(Order.user)
        )
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()

# Get orders by status — useful for filtering
@router.get("/status/{status}", response_model=List[TransactionResponse])
async def get_orders_by_status(
    status: TransactionStatus,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .where(
            Order.merchant_id == current_merchant.id,
            Order.status == status
        )
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()

# Get single order detail
@router.get("/{order_id}", response_model=TransactionResponse)
async def get_order_detail(
    order_id: int,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .where(
            Order.id == order_id,
            Order.merchant_id == current_merchant.id
        )
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Mark order as ready for pickup
@router.patch("/{order_id}/ready")
async def mark_ready_for_pickup(
    order_id: int,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .where(
            Order.id == order_id,
            Order.merchant_id == current_merchant.id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only paid orders can be marked ready
    if order.status != TransactionStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be paid before marking ready. Current status: '{order.status}'"
        )

    await update_transaction_status(db, order, TransactionStatus.READY_FOR_PICKUP)
    return {"message": "Order marked as ready for pickup"}

# Mark order as completed (user picked up)
@router.patch("/{order_id}/complete")
async def mark_completed(
    order_id: int,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .where(
            Order.id == order_id,
            Order.merchant_id == current_merchant.id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != TransactionStatus.READY_FOR_PICKUP:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be ready for pickup first. Current status: '{order.status}'"
        )

    await update_transaction_status(db, order, TransactionStatus.COMPLETED)
    return {"message": "Order marked as completed"}