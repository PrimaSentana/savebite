from datetime import datetime, timedelta, timezone
import decimal
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.menu import Menu, MenuStatus
from app.models.transaction import Order, TransactionStatus
from app.models.transaction_item import TransactionItem
from app.schemas.transaction import CheckoutRequest

def generate_order_id() -> str:
    return f"ORDER-{uuid.uuid4().hex[:12].upper()}"

async def get_transaction_by_order_id(db: AsyncSession, order_id: str):
    result = await db.execute(
        select(Order)
        .where(Order.order_id == order_id)
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()

async def get_transaction_by_id(db: AsyncSession, transaction_id: int):
    result = await db.execute(
        select(Order)
        .where(Order.id == transaction_id)
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()

async def get_user_transactions(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()

async def create_transaction(
    db: AsyncSession,
    user_id: int,
    data: CheckoutRequest,
    menus: list[Menu]
) -> Order:
    menu_map = {
        menu.id: menu for menu in menus
    }
    
    subtotal = decimal.Decimal("0")
    items_data = []
    
    for cart_item in data.items:
        menu = menu_map[cart_item.menu_id]
        item_subtotal = menu.discounted_price * cart_item.quantity
        subtotal += item_subtotal
        items_data.append({
            "menu_id": menu.id,
            "menu_title": menu.title,
            "menu_price": menu.discounted_price,
            "quantity": cart_item.quantity,
            "subtotal": item_subtotal
        })
    
    order = Order(
        order_id = generate_order_id(),
        user_id = user_id,
        merchant_id = menus[0].merchant_id,
        subtotal = subtotal,
        total_amount = subtotal,
        notes = data.notes,
        expired_at = datetime.now(timezone.utc) + timedelta(minutes=1)
    )
    db.add(order)
    await db.flush()
    
    for item_data in items_data:
        item = TransactionItem(transaction_id = order.id, **item_data)
        db.add(item)
    
    await db.commit()
    await db.refresh(order)
    return order

async def update_transaction_snap_token(
    db: AsyncSession,
    order: Order,
    snap_token: str,
    payment_url: str
):
    order.snap_token = snap_token
    order.payment_url = payment_url
    await db.commit()
    await db.refresh(order)
    return order

async def update_transaction_status(
    db: AsyncSession,
    order: Order,
    status: TransactionStatus,
    payment_type: str | None = None,
    midtrans_transaction_id: str | None = None
):
    order.status = status
    if payment_type:
        order.payment_type = payment_type
    if midtrans_transaction_id:
        order.midtrans_transaction_id = midtrans_transaction_id
    if status == TransactionStatus.PAID:
        order.paid_at = datetime.now(timezone.utc)
    if status == TransactionStatus.COMPLETED:
        order.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)
    return order

async def rollback_stock(db: AsyncSession, order: Order):
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    order_with_items = result.scalar_one_or_none()
    
    if not order_with_items:
        return
    
    for item in order_with_items.items:
        menu_result = await db.execute(
            select(Menu).where(Menu.id == item.menu_id)
        )
        menu = menu_result.scalar_one_or_none()
        
        if menu:
            menu.quantity += item.quantity
            if menu.status == MenuStatus.SOLD_OUT and menu.quantity > 0:
                menu.status = MenuStatus.ON_SALE
    
    await db.commit()