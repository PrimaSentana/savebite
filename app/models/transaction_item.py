# app/models/transaction_item.py
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base

class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)

    # Snapshot data — in case menu gets edited/deleted later, order history stays accurate
    menu_title = Column(String, nullable=False)
    menu_price = Column(Numeric(10, 2), nullable=False)  # price at time of purchase
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)    # menu_price * quantity

    # Relationships
    transaction = relationship("Order", back_populates="items")
    menu = relationship("Menu")