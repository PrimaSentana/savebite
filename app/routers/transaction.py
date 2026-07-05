import hashlib
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.menu import Menu, MenuStatus
from app.models.transaction import Order, TransactionStatus
from app.models.user import User
from app.schemas.transaction import CheckoutRequest, TransactionResponse
from app.crud import transaction as crud_transaction
from app.core.midtrans import snap, core_api
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/checkout", response_model=TransactionResponse, status_code=201)
async def checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Keranjang kosong")

    menu_ids = [item.menu_id for item in data.items]
    result = await db.execute(
        select(Menu).where(Menu.id.in_(menu_ids), Menu.is_active == True)
    )
    menus = result.scalars().all()
    
    if len(menus) != len(menu_ids):
        raise HTTPException(status_code=404, detail="Salah satu menu tidak ditemukan")
    
    merchant_ids = set(menu.merchant_id for menu in menus)
    if len(merchant_ids) > 1:
        raise HTTPException(status_code=400, detail="Menu harus berasal dari merchant yang sama")

    menu_map = {menu.id: menu for menu in menus}
    for cart_item in data.items:
        menu = menu_map[cart_item.menu_id]
        if menu.status == MenuStatus.SOLD_OUT:
            raise HTTPException(
                status_code=400,
                detail = f"'{menu.title}' sudah habis"
            )
        if cart_item.quantity > menu.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"'{menu.title}' hanya tersisa {menu.quantity}"
            )
        
    order = await crud_transaction.create_transaction(db, current_user.id, data, menus)
    
    for cart_item in data.items:
        menu = menu_map[cart_item.menu_id]
        menu.quantity -= cart_item.quantity
        if menu.quantity == 0:
            menu.status = MenuStatus.SOLD_OUT
    await db.commit()
    
    item_details = []
    for cart_item in data.items:
        menu = menu_map[cart_item.menu_id]
        item_details.append({
            "id": str(menu.id),
            "price": int(menu.discounted_price),
            "quantity": cart_item.quantity,
            "name": menu.title[:50]
        })
    
    midtrans_payload = {
        "transaction_details": {
            "order_id": order.order_id,
            "gross_amount": int(order.total_amount)
        },
        "item_details": item_details,
        "customer_details": {
            "first_name": current_user.username,
            "email": current_user.email
        },
        "expiry": {
            "unit": "hour",
            "duration": 1
        }
    }
    
    try:
        snap_response = snap.create_transaction(midtrans_payload)
        snap_token = snap_response["token"]
        payment_url = snap_response["redirect_url"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal membuat transaksi midtrans: {str(e)}"
        )
    
    order = await crud_transaction.update_transaction_snap_token(db, order, snap_token, payment_url)
    
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one()
    
    return order

#user order history
@router.get("/my-orders", response_model=List[TransactionResponse])
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await crud_transaction.get_user_transactions(db, current_user.id)

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_detail(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud_transaction.get_transaction_by_id(db, transaction_id)
    if not order:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak dapat akses")
    return order

@router.post("/{transaction_id}/cancel")
async def cancel_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud_transaction.get_transaction_by_id(db, transaction_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    if order.status != TransactionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Tidak bisa membatalkan transaksi dengan status '{order.status}"
        )
    
    try:
        core_api.transactions.cancel(order.order_id)
    except Exception as e:
        print(f"[Cancel] Midtrans cancel error: {e}")
    
    await crud_transaction.update_transaction_status(db, order, TransactionStatus.CANCELLED)
    await crud_transaction.rollback_stock(db, order)
    
    return {
        "message": "Transaksi berhasil dibatalkan"
    }

@router.post("/webhook/midtrans")
async def midtrans_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    body = await request.json()
    print(f"[Webhook] Received: {json.dumps(body, indent=2)}")
    
    order_id = body.get("order_id")
    transaction_status = body.get("transaction_status")
    fraud_status = body.get("fraud_status")
    payment_type = body.get("payment_type")
    midtrans_transaction_id = body.get("transaction_id")
    signature_key = body.get("signature_key")
    gross_amount = body.get("gross_amount")
    status_code = body.get("status_code")

    #test url midtrans
    # status_message = body.get("status_message")

    # if status_message != "midtrans payment notification":
    #     raw_string = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}"
    #     expected_signature = hashlib.sha512(raw_string.encode()).hexdigest()

    #     if signature_key != expected_signature:
    #         print("[Webhook] Invalid signature — possible fake notification!")
    #         raise HTTPException(status_code=403, detail="Invalid signature")

    # else:
    #     print("[Webhook] Test notification received from Midtrans Dashboard ✅")
    #     return {"message": "Test notification received"}
    
    raw_string = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}"
    expected_signature = hashlib.sha512(raw_string.encode()).hexdigest()

    if signature_key != expected_signature:
        print("[Webhook] Invalid signature — possible fake notification!")
        raise HTTPException(status_code=403, detail="Invalid signature")

    order = await crud_transaction.get_transaction_by_order_id(db, order_id)
    if not order:
        print(f"[Webhook] Order not found: {order_id}")
        raise HTTPException(status_code=403, detail="Order not found")
    
    finalized_statuses = [
        TransactionStatus.PAID,
        TransactionStatus.COMPLETED,
        TransactionStatus.CANCELLED,
    ]
    if order.status in finalized_statuses:
        print(f"[Webhook] Order {order_id} already finalized - skipping")
        return {
            "message": "Already finalized"
        }
    
    new_status = None
    should_rollback = False
    
    if transaction_status == "capture":
        if fraud_status == "accept":
            new_status = TransactionStatus.PAID
    elif transaction_status == "settlement":
        new_status = TransactionStatus.PAID
    elif transaction_status == "pending":
        new_status = TransactionStatus.PENDING
    elif transaction_status in ["deny", "cancel"]:
        new_status = TransactionStatus.CANCELLED
        should_rollback = True
    elif transaction_status == "expire":
        new_status = TransactionStatus.EXPIRED
        should_rollback = True
    elif transaction_status == "failure":
        new_status = TransactionStatus.FAILED
        should_rollback = True
        
    if new_status:
        await crud_transaction.update_transaction_status(
            db,
            order,
            new_status,
            payment_type = payment_type,
            midtrans_transaction_id = midtrans_transaction_id
        )
        print(f"[Webhook] Order {order_id} updated to {new_status}")
        
        if should_rollback:
            await crud_transaction.rollback_stock(db, order)
            print(f"[Webhook] Stock rolled back for order {order_id}")
    
    return {
        "message": "Webhook received"
    }