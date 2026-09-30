"""Capa 1 — Configuración de la aplicación.

Aquí se lee el entorno (`.env` + variables del sistema) y se convierte en
un objeto con sentido. Ninguna otra capa debe tocar `os.environ`.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfiguracionIncompleta(Exception):
    """Falta una variable de entorno obligatoria para arrancar."""


@dataclass(frozen=True)
class Configuracion:
    """Los valores con los que la aplicación funciona."""

    database_url: str


def cargar_configuracion() -> Configuracion:
    """Lee el entorno y devuelve la configuración de la aplicación.

    Falla ruidosamente si falta `DATABASE_URL`: es preferible un error claro
    al arrancar que un error de conexión cinco líneas más abajo.
    """
    load_dotenv()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ConfiguracionIncompleta(
            "Falta la variable de entorno DATABASE_URL. "
            "Copiá .env.example a .env y completá la cadena de conexión."
        )

    return Configuracion(database_url=database_url)