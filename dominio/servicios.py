"""Capa 2 — Reglas del catálogo.

Aquí vive lo que la tienda sabe hacer. No sabe de HTTP, no sabe de plantillas
y no abre conexiones: las recibe. Cuando una regla se cumple o se viola, se
dice con una excepción, y la capa 3 decide cómo mostrarlo.
"""

from dominio import repositorios


class ProductoDuplicado(Exception):
    """Regla violada: ya existe otro producto con ese nombre."""

    def __init__(self, nombre: str) -> None:
        super().__init__(f"Ya existe otro producto con el nombre {nombre!r}.")
        self.nombre = nombre


class ProductoNoEncontrado(Exception):
    """El producto que se intentó guardar no existe en la tabla."""

    def __init__(self, producto_id: int) -> None:
        super().__init__(f"No se encontró el producto con id {producto_id}.")
        self.producto_id = producto_id


async def listar_productos(conn) -> list[dict]:
    """Todos los productos del catálogo, ordenados por nombre."""
    return await repositorios.obtener_productos(conn)


async def crear_producto(
    conn,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> dict:
    """Crea un producto nuevo si el nombre no está duplicado."""
    nombre = (nombre or "").strip()
    if await repositorios.existe_producto_con_nombre(conn, nombre):
        raise ProductoDuplicado(nombre)

    producto_id = await repositorios.crear_producto(conn, nombre, precio, cantidad, descripcion)
    producto = await repositorios.obtener_producto(conn, producto_id)
    if producto is None:
        raise ProductoNoEncontrado(producto_id)
    return producto


async def obtener_producto(conn, producto_id: int) -> dict | None:
    """Un producto por su id, o None si no existe."""
    return await repositorios.obtener_producto(conn, producto_id)


async def eliminar_producto(conn, producto_id: int) -> None:
    """Borra un producto del catálogo."""
    await repositorios.eliminar_producto(conn, producto_id)


async def guardar_producto(
    conn,
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> dict:
    """Guarda los cambios de un producto y devuelve la fila ya actualizada.

    REGLA: no se pueden repetir nombres entre productos distintos.
    Si el nombre ya está en uso por otro producto, se lanza `ProductoDuplicado`
    y no se modifica nada en la base de datos.

    Si el id no existe, se lanza `ProductoNoEncontrado`.
    """
    if await repositorios.existe_producto_con_nombre(
        conn, nombre, excluir_id=producto_id
    ):
        raise ProductoDuplicado(nombre)

    actualizado = await repositorios.actualizar_producto(
        conn, producto_id, nombre, precio, cantidad, descripcion
    )
    if not actualizado:
        raise ProductoNoEncontrado(producto_id)

    producto = await repositorios.obtener_producto(conn, producto_id)
    if producto is None:
        raise ProductoNoEncontrado(producto_id)
    return producto