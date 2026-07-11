from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.menu import Menu, MenuStatus
from app.models.transaction import Order, TransactionStatus

scheduler = AsyncIOScheduler()

async def activate_menus():
    async with AsyncSessionLocal() as db:
        try:
            from app.models.menu import Menu, MenuStatus
            now = datetime.now(timezone.utc)
            
            result = await db.execute(
                update(Menu)
                .where(
                    Menu.available_from != None,
                    Menu.available_from <= now,
                    Menu.available_until > now,
                    Menu.is_active == False,
                    Menu.status == MenuStatus.HIDDEN,
                    Menu.quantity > 0
                )
                .values(
                    is_active=True,
                    status=MenuStatus.ON_SALE,
                )
                .execution_options(synchronize_session=False)
            )
            await db.commit()
            
            activated_count = result.rowcount
            if activated_count > 0:
                print(f"[Scheduler] {activated_count} menu(s) activated at {now}")
            else:
                print(f"[Scheduler] No menus to activate at {now}")

        except Exception as e:
            print(f"[Scheduler] Error activating menus: {e}")
            await db.rollback()

async def expire_menus():
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            
            result = await db.execute(
                update(Menu)
                .where(
                    Menu.available_until != None,
                    Menu.available_until <= now,
                    Menu.is_active == True,
                    Menu.status != MenuStatus.HIDDEN
                )
                .values(
                    is_active = False,
                    status = "hidden"
                ).execution_options(synchronize_session=False)
            )
            await db.commit()
            
            expired_count = result.rowcount
            if expired_count > 0:
                print(f"[Scheduler] {expired_count} menu(s) expired at {now}")
            else:
                print(f"[Scheduler] No expired menus found at {now}")
        except Exception as e:
            print(f"[Scheduler] Error: {e}")
            await db.rollback()
            
async def expire_abandoned_transactions():
    async with AsyncSessionLocal() as db:
        try:
            from app.models.menu import Menu, MenuStatus
            now = datetime.now(timezone.utc)
            
            result = await db.execute(
                select(Order)
                .where(
                    Order.status == TransactionStatus.PENDING,
                    Order.expired_at <= now
                )
                .options(selectinload(Order.items))
            )
            expired_orders = result.scalars().all()
            
            if not expired_orders:
                print(f"[Scheduler] No abandoned transactions found at {now}")
                return
            
            for order in expired_orders:
                order.status = TransactionStatus.EXPIRED
                for item in order.items:
                    menu_result = await db.execute(
                        select(Menu).where(Menu.id == item.menu_id)
                    )
                    menu = menu_result.scalar_one_or_none()
                    if menu:
                        menu.quantity += item.quantity
                        if menu.status == MenuStatus.SOLD_OUT and menu.quantity > 0:
                            menu.status = MenuStatus.ON_SALE
            await db.commit()
            print(f"[Scheduler] {len(expired_orders)} abandoned transaction(s) expired at {now}")
        except Exception as e:
            print(f"[Scheduler] Error expiring transactions: {e}")
            await db.rollback()

def start_scheduler():
    scheduler.add_job(
        expire_menus,
        trigger=IntervalTrigger(minutes=1),
        id="expire_menus",
        replace_existing=True
    )
    
    scheduler.add_job(
        expire_abandoned_transactions,
        trigger=IntervalTrigger(minutes=1),
        id="expire_abandoned_transactions",
        replace_existing=True
    )
    
    scheduler.add_job(
        activate_menus,
        trigger=IntervalTrigger(minutes=1),
        id="activate_menus",
        replace_existing=True
    )
    
    scheduler.start()
    print(f"[Scheduler] Started - checking activate, expired menus and abandoned transaction every 1 minute")