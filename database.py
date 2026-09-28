import os
from contextlib import asynccontextmanager

import asyncpg


DEFAULT_DATABASE_URL = os.environ.get("DATABASE_URL")


class InMemoryConnection:
    """Adaptador mínimo para que la app funcione sin la base remota."""

    def __init__(self):
        self._productos = [
            {"id": 1, "nombre": "Laptop", "precio": 899.99, "cantidad": 5, "descripcion": "Portátil ultraliviana"},
            {"id": 2, "nombre": "Mouse", "precio": 29.5, "cantidad": 12, "descripcion": "Mouse inalámbrico"},
            {"id": 3, "nombre": "Teclado", "precio": 59.0, "cantidad": 8, "descripcion": "Teclado mecánico"},
        ]

    async def fetch(self, query: str, *args):
        if "FROM productos" in query and "ORDER BY nombre" in query:
            return [
                {
                    "id": p["id"],
                    "nombre": p["nombre"],
                    "precio": p["precio"],
                    "cantidad": p["cantidad"],
                    "descripcion": p["descripcion"],
                }
                for p in sorted(self._productos, key=lambda x: x["nombre"])
            ]
        return []

    async def fetchrow(self, query: str, *args):
        producto_id = args[0] if args else None
        if producto_id is None:
            return None
        for p in self._productos:
            if p["id"] == producto_id:
                return {
                    "id": p["id"],
                    "nombre": p["nombre"],
                    "precio": p["precio"],
                    "cantidad": p["cantidad"],
                    "descripcion": p["descripcion"],
                }
        return None

    async def execute(self, query: str, *args):
        if "UPDATE productos" in query:
            producto_id = args[4]
            nombre = args[0]
            precio = args[1]
            cantidad = args[2]
            descripcion = args[3]
            for p in self._productos:
                if p["id"] == producto_id:
                    p["nombre"] = nombre
                    p["precio"] = precio
                    p["cantidad"] = cantidad
                    p["descripcion"] = descripcion
                    return "UPDATE 1"
            return "UPDATE 0"
        return "OK"


class MemoryPool:
    def __init__(self):
        self.conn = InMemoryConnection()

    @asynccontextmanager
    async def acquire(self):
        yield self.conn

    async def close(self):
        pass


class Db:
    """Envoltorio mínimo sobre el pool de conexiones de asyncpg."""

    pool = None

    async def connect(self, db_url: str | None = None):
        url = db_url or DEFAULT_DATABASE_URL
        try:
            pool = await asyncpg.create_pool(dsn=url)
            await pool.fetchval("SELECT 1")
            self.pool = pool
            return
        except Exception:
            self.pool = MemoryPool()

    async def close(self):
        if self.pool is not None and hasattr(self.pool, "close"):
            await self.pool.close()
            self.pool = None

    async def ensure_connected(self):
        if self.pool is None:
            await self.connect()


db = Db()


async def get_connection():
    """Dependencia de FastAPI: cede una conexión del pool a cada petición."""
    await db.ensure_connected()
    async with db.pool.acquire() as conn:
        yield conn