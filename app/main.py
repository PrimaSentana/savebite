from datetime import datetime
from time import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.scheluder import start_scheduler
from app.crud import merchants
from app.models import menu, merchants, transaction_item, transaction, user
from app.database import AsyncSessionLocal, engine, Base
from app.routers import auth, dashboard, menu, users, merchants, transaction as transaction_router

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
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code = 422,
        content = {
            "detail": exc.errors()
        }
    )
    
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
app.include_router(dashboard.router)  
app.include_router(merchants.router) 
app.include_router(menu.router)
app.include_router(transaction_router.router)

@app.get('/')
def test():
    return {
        "messsage": "Server started bitch!"
    }