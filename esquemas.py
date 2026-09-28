from pydantic import BaseModel, Field


class ProductoActualizar(BaseModel):
    """Datos válidos para actualizar un producto existente."""

    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio del producto")
    cantidad: int = Field(..., ge=0, description="Cantidad disponible")
    descripcion: str | None = None