from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.auth.router import router as auth_router
from src.properties.router import router as properties_router
from src.whatsapp.dependencies import get_whatsapp_service
from src.whatsapp.router import router as whatsapp_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    whatsapp = get_whatsapp_service()
    whatsapp.restore_all()
    try:
        yield
    finally:
        whatsapp.stop_all()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(properties_router)
