import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from nucleo.conexion import conexion
from presentacion.rutas.productos import router as productos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.environ.get("DATABASE_URL")
    await conexion.connect(database_url)
    yield
    await conexion.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def raiz():
    return RedirectResponse(url="/productos")


app.include_router(productos_router)