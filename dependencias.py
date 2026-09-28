from typing import Annotated

import asyncpg
from fastapi import Depends

from database import get_connection

# Así las vistas reciben la conexión de la base de datos como parámetro.
ConnectionDep = Annotated[asyncpg.Connection, Depends(get_connection)]