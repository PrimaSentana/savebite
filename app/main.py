from fastapi import FastAPI
from app.database import engine, Base
from app.models import user
from app.routers import auth, users

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
app.include_router(auth.router) 
app.include_router(users.router)       

@app.get('/')
def test():
    return {
        "messsage": "Server has Started"
    }