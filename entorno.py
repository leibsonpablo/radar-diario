"""Carga variables desde un archivo .env (sin dependencias externas)."""

import os
from pathlib import Path


def cargar_env(ruta: str = ".env") -> None:
    archivo = Path(__file__).parent / ruta
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        # Lo que ya está definido en el entorno (por ejemplo en GitHub Actions) tiene prioridad.
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))
