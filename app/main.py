from datetime import datetime
from time import time
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.admin.auth import AdminAuth
from app.admin.views import MenuAdmin, MerchantAdmin, OrderAdmin, ReviewAdmin, UserAdmin
from app.core.scheluder import start_scheduler
from app.crud import merchants
from app.models import menu, merchants, transaction_item, transaction, user, review
from app.database import AsyncSessionLocal, engine, Base
from app.routers import auth, dashboard, discovery, menu, merchant_transaction, users, merchants, transaction as transaction_router, review as review_router
from app.core.config import settings

app = FastAPI(title="SaveBite Super Ganas API")

app.add_middleware(SessionMiddleware, secret_key=settings.ADMIN_SECRET_KEY)
admin = Admin(
    app,
    engine,
    title="SaveBite Admin",
    authentication_backend=AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
)

admin.add_view(UserAdmin)
admin.add_view(MerchantAdmin)
admin.add_view(MenuAdmin)
admin.add_view(OrderAdmin)
admin.add_view(ReviewAdmin)

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
app.include_router(discovery.router)
app.include_router(merchants.router)
app.include_router(merchant_transaction.router)
app.include_router(menu.router)
app.include_router(transaction_router.router)
app.include_router(review_router.router)


@app.get('/')
def test():
    return {
        "messsage": "Server started bitch!"
    }