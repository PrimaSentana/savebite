from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.merchants import extract_location, get_nearby_merchants
from app.database import get_db
from app.schemas.merchants import NearbyMerchantResponse


router = APIRouter(prefix="/discovery", tags=["Discovery"])

def format_distance(meters: float) -> str:
    if meters < 1000:
        return f"{int(meters)} m"
    else:
        return f"{meters / 1000:.1f} km"
    
@router.get("/nearby-merchants", response_model=List[NearbyMerchantResponse])
async def get_nearby_merchants_endpoint(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: float = Query(5000, description="Search radius in meters (default km)"),
    db: AsyncSession = Depends(get_db)
):
    rows = await get_nearby_merchants(db, latitude, longitude, radius)
    
    response = []
    for row in rows:
        merchant = row[0]
        distance_meters = float(row[1])
        available_menu_count = row[2]
        
        location = extract_location(merchant)
        
        response.append(NearbyMerchantResponse(
            id = merchant.id,
            name = merchant.name,
            description = merchant.description,
            logo_url = merchant.logo_url,
            banner_url = merchant.banner_url,
            address = merchant.address,
            latitude = location["latitude"],
            longitude = location["longitude"],
            distance_meters = round(distance_meters, 2),
            distance_text = format_distance(distance_meters),
            is_active = merchant.is_active,
            available_menu_count = available_menu_count,
        ))
    return response