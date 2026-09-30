from pydantic import BaseModel, Field


class ProductoActualizar(BaseModel):
    """Datos que el estudiante envía al editar un producto."""
    nombre: str = Field(min_length=1, max_length=100)
    precio: float = Field(gt=0)
    cantidad: int = Field(ge=0)
    descripcion: str | None = None