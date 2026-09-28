from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencias import ConnectionDep
from esquemas import ProductoActualizar
from repositorio import (
    actualizar_producto,
    crear_producto,
    eliminar_producto,
    obtener_producto,
    obtener_productos,
)

router = APIRouter(tags=["productos"])

templates = Jinja2Templates(directory="templates")


@router.get("/productos")
async def listar_productos(request: Request, conn: ConnectionDep):
    productos = await obtener_productos(conn)
    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={"productos": productos},
    )


@router.get("/productos/nuevo")
async def nuevo_producto_vista(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="nuevo_producto.html",
        context={
            "nombre": "",
            "precio": "",
            "cantidad": "",
            "descripcion": "",
            "errores": {},
        },
    )


@router.post("/productos/nuevo")
async def crear_nuevo_producto(
    request: Request,
    conn: ConnectionDep,
    nombre: Annotated[str | None, Form()] = None,
    precio: Annotated[str | None, Form()] = None,
    cantidad: Annotated[str | None, Form()] = None,
    descripcion: Annotated[str | None, Form()] = None,
):
    errores: dict[str, str] = {}

    precio_num: float | None = None
    if precio is not None and precio.strip() != "":
        try:
            precio_num = float(precio)
        except ValueError:
            errores["precio"] = "El precio debe ser un número."
    else:
        errores["precio"] = "El precio es obligatorio."

    cantidad_num: int | None = None
    if cantidad is not None and cantidad.strip() != "":
        try:
            cantidad_num = int(cantidad)
        except ValueError:
            errores["cantidad"] = "La cantidad debe ser un número entero."
    else:
        errores["cantidad"] = "La cantidad es obligatoria."

    if not errores:
        try:
            ProductoActualizar(
                nombre=nombre or "",
                precio=precio_num,
                cantidad=cantidad_num,
                descripcion=descripcion,
            )
        except ValidationError as exc:
            for error in exc.errors():
                campo = str(error["loc"][0])
                errores[campo] = error["msg"]

    if errores:
        return templates.TemplateResponse(
            request=request,
            name="nuevo_producto.html",
            context={
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
                "errores": errores,
            },
            status_code=422,
        )

    nuevo_id = await crear_producto(conn, nombre.strip(), precio_num, cantidad_num, descripcion)
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_actualizada.html",
        context={"producto": await obtener_producto(conn, nuevo_id)},
    )


@router.get("/productos/{producto_id}/editar")
async def editar_producto_vista(request: Request, conn: ConnectionDep, producto_id: int):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return templates.TemplateResponse(
        request=request,
        name="editar_producto.html",
        context={
            "producto": producto,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": producto["cantidad"],
            "descripcion": producto["descripcion"],
            "errores": {},
        },
    )


@router.get("/productos/{producto_id}/cancelar")
async def cancelar_edicion_vista(request: Request, conn: ConnectionDep, producto_id: int):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_producto.html",
        context={"producto": producto},
    )


@router.post("/productos/{producto_id}/eliminar")
async def eliminar_producto_vista(request: Request, conn: ConnectionDep, producto_id: int):
    eliminado = await eliminar_producto(conn, producto_id)
    if not eliminado:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return RedirectResponse(url="/productos", status_code=303)


@router.post("/productos/{producto_id}")
async def guardar_producto_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,
    nombre: Annotated[str | None, Form()] = None,
    precio: Annotated[str | None, Form()] = None,
    cantidad: Annotated[str | None, Form()] = None,
    descripcion: Annotated[str | None, Form()] = None,
):
    errores: dict[str, str] = {}

    # 1. Convertir precio y cantidad a número, guardando un error si el
    #    texto recibido no se puede convertir (por ejemplo, vacío o "abc").
    precio_num: float | None = None
    if precio is not None and precio.strip() != "":
        try:
            precio_num = float(precio)
        except ValueError:
            errores["precio"] = "El precio debe ser un número."
    else:
        errores["precio"] = "El precio es obligatorio."

    cantidad_num: int | None = None
    if cantidad is not None and cantidad.strip() != "":
        try:
            cantidad_num = int(cantidad)
        except ValueError:
            errores["cantidad"] = "La cantidad debe ser un número entero."
    else:
        errores["cantidad"] = "La cantidad es obligatoria."

    # 2. Si la conversión básica funcionó, validamos con el esquema de
    #    Pydantic (nombre obligatorio, precio > 0, cantidad >= 0).
    producto_validado = None
    if not errores:
        try:
            producto_validado = ProductoActualizar(
                nombre=nombre or "",
                precio=precio_num,
                cantidad=cantidad_num,
                descripcion=descripcion,
            )
        except ValidationError as exc:
            for error in exc.errors():
                campo = str(error["loc"][0])
                errores[campo] = error["msg"]

    # 3. Si hay errores, no se toca la base de datos: se vuelve a mostrar
    #    el formulario con lo que el usuario escribió (no los valores
    #    originales) y código 422.
    if errores:
        return templates.TemplateResponse(
            request=request,
            name="editar_producto.html",
            context={
                "producto": {"id": producto_id},
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
                "errores": errores,
            },
            status_code=422,
        )

    # 4. Datos válidos: ejecutamos el UPDATE identificando el registro
    #    solo por su id.
    actualizado = await actualizar_producto(
        conn,
        producto_id,
        producto_validado.nombre,
        producto_validado.precio,
        producto_validado.cantidad,
        producto_validado.descripcion,
    )

    if not actualizado:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )

    producto = await obtener_producto(conn, producto_id)
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_actualizada.html",
        context={"producto": producto},
    )