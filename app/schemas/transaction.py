from datetime import datetime
import decimal

from pydantic import BaseModel

from app.models.transaction import TransactionStatus


class CartItem(BaseModel):
    menu_id: int
    quantity: int

class CheckoutRequest(BaseModel):
    items: list[CartItem]
    notes: str | None = None

class TransactionItemResponse(BaseModel):
    id: int
    menu_id: int
    menu_title: str
    menu_price: decimal.Decimal
    quantity: int
    subtotal: decimal.Decimal
    
    class config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    order_id: str
    user_id: int
    merchant_id: int
    subtotal: decimal.Decimal
    total_amount: decimal.Decimal
    status: TransactionStatus
    snap_token: str | None = None
    payment_type: str | None = None
    notes: str | None = None
    paid_at: datetime | None = None
    expired_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    items: list[TransactionItemResponse] = []
    customer_username: str | None = None
    
    class config:
        from_attributes = True