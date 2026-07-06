from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired" 
    FAILED = "failed"
    CANCELLED = "cancelled"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"

class Order(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)

    subtotal = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)

    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)

    snap_token = Column(String, nullable=True)
    payment_type = Column(String, nullable=True)
    payment_url = Column(String, nullable=True)
    midtrans_transaction_id = Column(String, nullable=True)

    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    review = relationship("Review", back_populates="transaction", uselist=False)
    
    @property
    def customer_username(self) -> str | None:
        return self.user.username if self.user else None