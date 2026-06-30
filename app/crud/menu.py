import cloudinary
import cloudinary.uploader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.models.menu import Menu, MenuStatus
from app.models.merchants import Merchant
from app.schemas.menu import MenuCreate, MenuUpdate
import decimal

def calculate_discount_percentage(
    original: decimal.Decimal,
    discounted: decimal.Decimal
) -> decimal.Decimal:
    return round(((original - discounted) / original) * 100, 2)


async def get_menus_by_merchant(db: AsyncSession, merchant_id: int):
    result = await db.execute(
        select(Menu)
        .where(Menu.merchant_id == merchant_id) #catatan untuk kondisi aktif dan non-aktif
        .order_by(Menu.created_at.desc())
    )
    return result.scalars().all()

async def get_all_menu(db: AsyncSession) -> list[Menu]:
    result = await db.execute(select(Menu))
    return result.scalars().all()


async def get_menu_by_id(db: AsyncSession, menu_id: int):
    result = await db.execute(
        select(Menu).where(Menu.id == menu_id) #catatan untuk kondisi aktif dan non-aktif
    )
    return result.scalar_one_or_none()

async def get_menu_by_id_deactive(db: AsyncSession, menu_id: int):
    result = await db.execute(
        select(Menu).where(Menu.id == menu_id, Menu.is_active == False)
    )
    return result.scalar_one_or_none()

async def create_menu(db: AsyncSession, merchant_id: int, data: MenuCreate):
    discount_pct = calculate_discount_percentage(
        data.original_price,
        data.discounted_price
    )
    menu = Menu(
        merchant_id=merchant_id,
        title=data.title,
        description=data.description,
        category=data.category,
        original_price=data.original_price,
        discounted_price=data.discounted_price,
        discount_percentage=discount_pct,
        quantity=data.quantity,
        max_order_per_user=data.quantity,
        available_from=data.available_from,
        available_until=data.available_until,
    )
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return menu

async def update_menu(db: AsyncSession, menu: Menu, data: MenuUpdate):
    update_data = data.model_dump(exclude_none=True)

    original = update_data.get("original_price", menu.original_price)
    discounted = update_data.get("discounted_price", menu.discounted_price)
    if "original_price" in update_data or "discounted_price" in update_data:
        update_data["discount_percentage"] = calculate_discount_percentage(
            original, discounted
        )

    for field, value in update_data.items():
        setattr(menu, field, value)

    if menu.quantity == 0:
        menu.status = MenuStatus.SOLD_OUT

    await db.commit()
    await db.refresh(menu)
    return menu

async def activated_menu(db: AsyncSession, menu: Menu):
    menu.is_active = True
    await db.commit()
    
async def deactive_menu(db: AsyncSession, menu: Menu):
    menu.is_active = False
    await db.commit()
    
async def delete_menu(db: AsyncSession, menu: Menu):
    await db.delete(menu)
    await db.commit()

async def bulk_delete_menu(db: AsyncSession, merchant_id: int, menu_ids: list[int]):
    result = await db.execute(
        delete(Menu)
        .where(
            Menu.id.in_(menu_ids),
            Menu.merchant_id == merchant_id
        ).execution_options(synchronize_session=False)
    )
    await db.commit()
    return result.rowcount

