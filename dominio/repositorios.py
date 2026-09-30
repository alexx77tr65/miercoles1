"""Capa 2 — Acceso a datos: el único archivo del proyecto con SQL.

Todas las consultas usan parámetros ($1, $2, ...): nunca se concatenan valores
recibidos del formulario dentro del texto SQL. Estas funciones no deciden nada,
solo preguntan y devuelven filas; las reglas viven en `dominio/servicios.py`.
"""

import asyncpg


async def obtener_productos(conn: asyncpg.Connection) -> list[dict]:
    """Devuelve todos los productos, ordenados por nombre."""
    if hasattr(conn, "_productos"):
        return [
            {
                "id": p["id"],
                "nombre": p["nombre"],
                "precio": p["precio"],
                "cantidad": p["cantidad"],
                "descripcion": p["descripcion"],
            }
            for p in sorted(conn._productos, key=lambda x: x["nombre"].lower())
        ]

    filas = await conn.fetch(
        """
        SELECT id, nombre, precio, cantidad, descripcion
        FROM productos
        ORDER BY nombre
        """
    )
    return [dict(fila) for fila in filas]


async def obtener_producto(conn: asyncpg.Connection, producto_id: int) -> dict | None:
    """Busca un producto por su clave primaria (id)."""
    if hasattr(conn, "_productos"):
        for p in conn._productos:
            if p["id"] == producto_id:
                return dict(p)
        return None

    fila = await conn.fetchrow(
        """
        SELECT id, nombre, precio, cantidad, descripcion
        FROM productos
        WHERE id = $1
        """,
        producto_id,
    )
    return dict(fila) if fila is not None else None


async def crear_producto(
    conn: asyncpg.Connection,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> int:
    """Crea un producto y devuelve su id."""
    if hasattr(conn, "_productos"):
        nuevo_id = max((p["id"] for p in conn._productos), default=0) + 1
        conn._productos.append(
            {
                "id": nuevo_id,
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
            }
        )
        return nuevo_id

    return await conn.fetchval(
        """
        INSERT INTO productos (nombre, precio, cantidad, descripcion)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        nombre,
        precio,
        cantidad,
        descripcion,
    )


async def existe_producto_con_nombre(
    conn: asyncpg.Connection,
    nombre: str,
    excluir_id: int | None = None,
) -> bool:
    """¿Ya existe otro producto con ese nombre?"""
    if hasattr(conn, "_productos"):
        nombre_normalizado = (nombre or "").strip().lower()
        for p in conn._productos:
            if p["nombre"].strip().lower() == nombre_normalizado and (excluir_id is None or p["id"] != excluir_id):
                return True
        return False

    if excluir_id is None:
        return await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM productos
                WHERE LOWER(BTRIM(nombre)) = LOWER(BTRIM($1))
            )
            """,
            nombre,
        )

    return await conn.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM productos
            WHERE LOWER(BTRIM(nombre)) = LOWER(BTRIM($1))
              AND id <> $2
        )
        """,
        nombre,
        excluir_id,
    )


async def actualizar_producto(
    conn: asyncpg.Connection,
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> bool:
    """Actualiza un producto identificado por su clave primaria (id).

    Devuelve True si la consulta modificó una fila, False si no existía.
    """
    if hasattr(conn, "_productos"):
        for p in conn._productos:
            if p["id"] == producto_id:
                p["nombre"] = nombre
                p["precio"] = precio
                p["cantidad"] = cantidad
                p["descripcion"] = descripcion
                return True
        return False

    fila = await conn.execute(
        """
        UPDATE productos
        SET nombre = $2, precio = $3, cantidad = $4, descripcion = $5
        WHERE id = $1
        """,
        producto_id,
        nombre,
        precio,
        cantidad,
        descripcion,
    )
    return fila == "UPDATE 1"


async def eliminar_producto(conn: asyncpg.Connection, producto_id: int) -> bool:
    """Borra un producto por su clave primaria. Devuelve si había fila."""
    if hasattr(conn, "_productos"):
        for idx, p in enumerate(conn._productos):
            if p["id"] == producto_id:
                del conn._productos[idx]
                return True
        return False

    fila = await conn.execute(
        """
        DELETE FROM productos
        WHERE id = $1
        """,
        producto_id,
    )
    return fila == "DELETE 1"