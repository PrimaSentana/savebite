from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu import Menu, MenuStatus
from app.models.merchants import Merchant
from app.schemas.search import SearchParams

async def search_merchants(
    db: AsyncSession,
    params: SearchParams
):
    query = select(
        Merchant,
        select(func.count())
        .where(
            and_(
                Menu.merchant_id == Merchant.id,
                Menu.is_active == True,
                Menu.status == MenuStatus.ON_SALE,
                Menu.quantity > 0
            )
        )
        .scalar_subquery()
        .label("available_menu_count")
    ).where(Merchant.is_active == True)
    
    if params.keyword:
        query = query.where(
            Merchant.name.ilike(f"%{params.keyword}%")
        )
    
    has_active_menu = (
        select(Menu)
        .where(
            and_(
                Menu.merchant_id == Merchant.id,
                Menu.is_active == True,
                Menu.status == MenuStatus.ON_SALE,
                Menu.quantity > 0
            )
        )
        .exists()
    )
    query = query.where(has_active_menu)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": row[0].id,
            "name": row[0].name,
            "description": row[0].description,
            "logo_url": row[0].logo_url,
            "banner_url": row[0].banner_url,
            "address": row[0].address,
            "is_active": row[0].is_active,
            "available_menu_count": row[1],
        }
        for row in rows
    ]

async def search_menus(
    db: AsyncSession,
    params: SearchParams
):
    query = select(Menu, Merchant).join(
        Merchant, Menu.merchant_id == Merchant.id
    ).where(
        Menu.is_active == True,
        Menu.status == MenuStatus.ON_SALE,
        Menu.quantity > 0,
        Merchant.is_active == True
    )
    
    if params.keyword:
        query = query.where(
            or_(
                Menu.title.ilike(f"%{params.keyword}%"),
                Menu.description.ilike(f"%{params.keyword}%")
            )
        )
    
    if params.category:
        query = query.where(Menu.category == params.category)
    
    if params.max_price:
        query = query.where(Menu.discounted_price <= params.max_price)
        
    if params.min_discount:
        query = query.where(Menu.discount_percentage >= params.min_discount)
    
    if params.sort_by == "discount":
        query = query.order_by(Menu.discount_percentage.desc())
    elif params.sort_by == "price_asc":
        query = query.order_by(Menu.discounted_price.asc())
    elif params.sort_by == "price_desc":
        query = query.order_by(Menu.discounted_price.desc())
    elif params.sort_by == "newest":
        query = query.order_by(Menu.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": row[0].id,
            "merchant_id": row[0].merchant_id,
            "merchant_name": row[1].name,
            "merchant_logo": row[1].logo_url,
            "title": row[0].title,
            "description": row[0].description,
            "image_url": row[0].image_url,
            "category": row[0].category,
            "original_price": float(row[0].original_price),
            "discounted_price": float(row[0].discounted_price),
            "discount_percentage": float(row[0].discount_percentage) if row[0].discount_percentage else None,
            "quantity": row[0].quantity,
        }
        for row in rows
    ]