import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse  # Importante

from database import db
from vistas import router as vistas_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        await db.connect(database_url)
    else:
        await db.connect(None)
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def raiz():
    return RedirectResponse(url="/productos")

app.include_router(vistas_router)