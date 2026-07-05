from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Boolean, DateTime, null
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
# from shapely.geometry import Point
from app.database import Base

class Merchant(Base):
    __tablename__ = "merchants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    is_active = Column(Boolean, default=True)
    is_open = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    menus = relationship("Menu", back_populates="merchant", cascade="all, delete-orphan")
    
    transactions = relationship("Order", back_populates="merchant")