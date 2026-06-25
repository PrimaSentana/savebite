from fastapi import FastAPI
from app.crud import merchants
from app.database import engine, Base
from app.routers import auth, menu, users, merchants

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
app.include_router(auth.router) 
app.include_router(users.router)      
app.include_router(merchants.router) 
app.include_router(menu.router)

@app.get('/')
def test():
    return {
        "messsage": "Server has Started"
    }