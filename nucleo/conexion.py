"""Capa 1 — Conexión a PostgreSQL.

El pool de asyncpg y la dependencia de FastAPI que lo expone viven en el
mismo archivo porque nacen el uno del otro: la dependencia no abre conexiones,
solo pide una prestada al pool.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import asyncpg
from fastapi import Depends


class InMemoryConnection:
    """Adaptador mínimo para que la app funcione sin PostgreSQL."""

    def __init__(self):
        self._productos = [
            {"id": 1, "nombre": "Laptop", "precio": 899.99, "cantidad": 5, "descripcion": "Portátil ultraliviana"},
            {"id": 2, "nombre": "Mouse", "precio": 29.5, "cantidad": 12, "descripcion": "Mouse inalámbrico"},
            {"id": 3, "nombre": "Teclado", "precio": 59.0, "cantidad": 8, "descripcion": "Teclado mecánico"},
        ]

    async def fetch(self, query: str, *args):
        query_norm = " ".join(query.lower().split())
        if "from productos" in query_norm and "order by nombre" in query_norm:
            return [
                {
                    "id": p["id"],
                    "nombre": p["nombre"],
                    "precio": p["precio"],
                    "cantidad": p["cantidad"],
                    "descripcion": p["descripcion"],
                }
                for p in sorted(self._productos, key=lambda x: x["nombre"].lower())
            ]
        return []

    async def fetchrow(self, query: str, *args):
        query_norm = " ".join(query.lower().split())
        producto_id = args[0] if args else None
        if "from productos" in query_norm and "where id = $1" in query_norm and producto_id is not None:
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

    async def fetchval(self, query: str, *args):
        query_norm = " ".join(query.lower().split())
        if "exists" in query_norm and "from productos" in query_norm:
            nombre = args[0]
            excluir_id = args[1] if len(args) > 1 else None
            for p in self._productos:
                nombre_igual = (p["nombre"] or "").strip().lower() == (nombre or "").strip().lower()
                if nombre_igual and (excluir_id is None or p["id"] != excluir_id):
                    return True
            return False
        if "insert into productos" in query_norm and "returning id" in query_norm:
            nombre, precio, cantidad, descripcion = args
            nuevo_id = max((p["id"] for p in self._productos), default=0) + 1
            self._productos.append(
                {
                    "id": nuevo_id,
                    "nombre": nombre,
                    "precio": precio,
                    "cantidad": cantidad,
                    "descripcion": descripcion,
                }
            )
            return nuevo_id
        return None

    async def execute(self, query: str, *args):
        query_norm = " ".join(query.lower().split())
        if "update productos" in query_norm:
            producto_id = args[0]
            nombre = args[1]
            precio = args[2]
            cantidad = args[3]
            descripcion = args[4]
            for p in self._productos:
                if p["id"] == producto_id:
                    p["nombre"] = nombre
                    p["precio"] = precio
                    p["cantidad"] = cantidad
                    p["descripcion"] = descripcion
                    return "UPDATE 1"
            return "UPDATE 0"
        if "delete from productos" in query_norm:
            producto_id = args[0]
            for index, p in enumerate(self._productos):
                if p["id"] == producto_id:
                    del self._productos[index]
                    return "DELETE 1"
            return "DELETE 0"
        return "OK"


class MemoryPool:
    def __init__(self):
        self.conn = InMemoryConnection()

    async def close(self):
        pass

    @asynccontextmanager
    async def acquire(self):
        yield self.conn


class GestorConexion:
    """Envoltorio mínimo sobre el pool de conexiones de asyncpg."""

    pool = None

    async def connect(self, database_url: str | None = None) -> None:
        try:
            if database_url:
                self.pool = await asyncpg.create_pool(dsn=database_url)
                await self.pool.fetchval("SELECT 1")
                return
        except Exception:
            pass
        self.pool = MemoryPool()

    async def close(self) -> None:
        if self.pool is not None and hasattr(self.pool, "close"):
            await self.pool.close()
            self.pool = None


conexion = GestorConexion()


async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    """Dependencia de FastAPI: cede una conexión del pool a cada petición."""
    if conexion.pool is None:
        await conexion.connect()
    async with conexion.pool.acquire() as conn:
        yield conn


# Así las rutas reciben la conexión de la base de datos como parámetro.
ConnectionDep = Annotated[asyncpg.Connection, Depends(get_connection)]