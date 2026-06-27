from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models.menu import Menu, MenuStatus

scheduler = AsyncIOScheduler()

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
                    Menu.status != "sold_out"
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

def start_scheduler():
    scheduler.add_job(
        expire_menus,
        trigger=IntervalTrigger(minutes=5),
        id="expire_menus",
        replace_existing=True
    )
    scheduler.start()
    print(f"[Scheduler] Started - checking expired menus every 1 minute")