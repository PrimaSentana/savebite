# app/models/menu.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class MenuCategory(str, enum.Enum):
    FOOD = "food"
    BEVERAGE = "beverage"
    SNACK = "snack"
    DESSERT = "dessert"
    OTHER = "other"

class MenuStatus(str, enum.Enum):
    ON_SALE = "on_sale"
    SOLD_OUT = "sold_out"
    HIDDEN = "hidden"

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    category = Column(Enum(MenuCategory), nullable=False, default=MenuCategory.FOOD)
    original_price = Column(Numeric(10, 2), nullable=False)   
    discounted_price = Column(Numeric(10, 2), nullable=False) 
    discount_percentage = Column(Numeric(5, 2), nullable=True) 
    quantity = Column(Integer, nullable=False, default=0)      
    max_order_per_user = Column(Integer, nullable=True)
    status = Column(Enum(MenuStatus), nullable=False, default=MenuStatus.ON_SALE)
    is_active = Column(Boolean, default=True)
    available_from = Column(DateTime(timezone=True), nullable=True)  
    available_until = Column(DateTime(timezone=True), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    merchant = relationship("Merchant", back_populates="menus")