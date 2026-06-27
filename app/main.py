from datetime import datetime
from time import time

from fastapi import FastAPI
from app.core.scheluder import start_scheduler
from app.crud import merchants
from app.database import AsyncSessionLocal, engine, Base
from app.routers import auth, menu, users, merchants

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    start_scheduler()
    
@app.on_event("shutdown")
async def shutdown():
    from app.core.scheluder import scheduler
    from app.database import AsyncSessionLocal
    scheduler.shutdown()
    print("[Scheduler] Stopped")
    await AsyncSessionLocal().close()
    
@app.get("/sys-info/timezone")
def check_timezone():
    local_time = datetime.now().astimezone()
    
    return {
        "timezone_name": time(),
        "tz_info": str(local_time.tzinfo),
        "current_time_iso": local_time.isoformat(),
        "utc_offset_hours": local_time.utcoffset().total_seconds() / 3600
    }
        
app.include_router(auth.router) 
app.include_router(users.router)      
app.include_router(merchants.router) 
app.include_router(menu.router)

@app.get('/')
def test():
    return {
        "messsage": "Server started bitch!"
    }