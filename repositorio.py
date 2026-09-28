# Este archivo concentra todas las consultas SQL del ejercicio.
# Todas usan parámetros ($1, $2, ...): nunca se concatenan valores
# recibidos del formulario dentro del texto SQL.


async def obtener_productos(conn) -> list[dict]:
    """Devuelve todos los productos, ordenados por nombre."""
    filas = await conn.fetch(
        "SELECT id, nombre, precio, cantidad, descripcion "
        "FROM productos ORDER BY nombre"
    )
    return [dict(fila) for fila in filas]


async def obtener_producto(conn, producto_id: int) -> dict | None:
    """Busca un producto por su clave primaria (id)."""
    fila = await conn.fetchrow(
        "SELECT id, nombre, precio, cantidad, descripcion "
        "FROM productos WHERE id = $1",
        producto_id,
    )
    return dict(fila) if fila is not None else None


async def crear_producto(
    conn,
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


async def actualizar_producto(
    conn,
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
        for producto in conn._productos:
            if producto["id"] == producto_id:
                producto["nombre"] = nombre
                producto["precio"] = precio
                producto["cantidad"] = cantidad
                producto["descripcion"] = descripcion
                return True
        return False

    resultado = await conn.execute(
        """
        UPDATE productos
        SET nombre = $1, precio = $2, cantidad = $3, descripcion = $4
        WHERE id = $5
        """,
        nombre,
        precio,
        cantidad,
        descripcion,
        producto_id,
    )
    # asyncpg devuelve "UPDATE 1" si modificó una fila, "UPDATE 0" si no.
    return resultado == "UPDATE 1"


async def eliminar_producto(conn, producto_id: int) -> bool:
    """Elimina un producto por su id y devuelve True si se eliminó."""
    if hasattr(conn, "_productos"):
        for idx, producto in enumerate(conn._productos):
            if producto["id"] == producto_id:
                del conn._productos[idx]
                return True
        return False

    resultado = await conn.execute(
        "DELETE FROM productos WHERE id = $1",
        producto_id,
    )
    return resultado == "DELETE 1"