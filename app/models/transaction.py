# app/models/transaction.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"           # waiting for payment
    PAID = "paid"                 # payment successful
    EXPIRED = "expired"           # user didn't pay in time
    FAILED = "failed"             # payment failed
    CANCELLED = "cancelled"       # user/merchant cancelled
    READY_FOR_PICKUP = "ready_for_pickup"  # merchant prepared the order
    COMPLETED = "completed"       # user picked up the order

class Order(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, nullable=False)  # sent to Midtrans
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)

    subtotal = Column(Numeric(10, 2), nullable=False)     # total before fees
    total_amount = Column(Numeric(10, 2), nullable=False) # final amount paid

    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)

    # Midtrans related fields
    snap_token = Column(String, nullable=True)
    payment_type = Column(String, nullable=True)      # e.g. "bank_transfer", "gopay", "qris"
    payment_url = Column(String, nullable=True)        # snap redirect url (optional)
    midtrans_transaction_id = Column(String, nullable=True)

    notes = Column(Text, nullable=True)  # buyer notes, e.g. "less spicy"
    paid_at = Column(DateTime(timezone=True), nullable=True)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")