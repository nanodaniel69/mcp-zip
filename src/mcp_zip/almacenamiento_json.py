"""Almacenamiento JSON como store secundario estructurado.

Los .md son el store primario (git-friendly, human-readable).
Los .json son el cache estructurado (parseo rápido, acceso programático).

Flujo:
  .md  →  .json  →  SQLite
  store   cache     índice
"""

import json
from pathlib import Path
from typing import Optional

from .configuracion import config
from .formateador import Entrada, parsear_archivo


# Mapeo de tipos de archivo a nombres JSON
ARCHIVOS_JSON = {
    "resumen": "RESUMEN.json",
    "errores": "errores.json",
    "decisiones": "decisiones.json",
    "implementacion": "implementacion.json",
    "plan": "plan.json",
}


def ruta_json(proyecto: str, tipo_archivo: str) -> Path:
    """Obtiene la ruta del archivo JSON para un tipo dado."""
    if tipo_archivo in ARCHIVOS_JSON:
        filename = ARCHIVOS_JSON[tipo_archivo]
    else:
        filename = f"{tipo_archivo}.json"
    return config.proyecto_dir(proyecto) / filename


def leer_json(proyecto: str, tipo_archivo: str) -> list[dict]:
    """Lee un archivo JSON y devuelve la lista de entradas."""
    path = ruta_json(proyecto, tipo_archivo)
    if not path.exists():
        return []
    try:
        contenido = path.read_text(encoding=config.encoding)
        datos = json.loads(contenido)
        if isinstance(datos, list):
            return datos
        return []
    except (json.JSONDecodeError, TypeError):
        return []


def escribir_json(proyecto: str, tipo_archivo: str, entradas: list[dict]):
    """Escribe una lista de entradas en formato JSON."""
    path = ruta_json(proyecto, tipo_archivo)
    path.parent.mkdir(parents=True, exist_ok=True)
    contenido = json.dumps(entradas, ensure_ascii=False, indent=2)
    path.write_text(contenido, encoding=config.encoding)


def entrada_a_dict(entrada: Entrada) -> dict:
    """Convierte un objeto Entrada a diccionario para JSON."""
    return {
        "id": entrada.id,
        "tipo": entrada.tipo,
        "titulo": entrada.titulo,
        "fecha": entrada.fecha,
        "estado": entrada.estado,
        "contenido": entrada.contenido,
        "etiquetas": entrada.etiquetas,
        "archivos_afectados": entrada.archivos_afectados,
        "proyecto": entrada.proyecto,
        "archivado": entrada.archivado,
        "fecha_archivado": entrada.fecha_archivado,
    }


def dict_a_entrada(d: dict) -> Entrada:
    """Convierte un diccionario JSON a objeto Entrada."""
    return Entrada(
        id=d.get("id", ""),
        tipo=d.get("tipo", ""),
        titulo=d.get("titulo", ""),
        fecha=d.get("fecha", ""),
        estado=d.get("estado", ""),
        contenido=d.get("contenido", {}),
        etiquetas=d.get("etiquetas", []),
        archivos_afectados=d.get("archivos_afectados", []),
        proyecto=d.get("proyecto", ""),
        archivado=d.get("archivado", False),
        fecha_archivado=d.get("fecha_archivado", ""),
    )


def agregar_entrada_json(proyecto: str, tipo_archivo: str, entrada: Entrada):
    """Agrega una entrada al archivo JSON correspondiente."""
    entradas = leer_json(proyecto, tipo_archivo)
    nueva = entrada_a_dict(entrada)

    # Si ya existe una entrada con el mismo ID, reemplazar
    entradas = [e for e in entradas if e.get("id") != entrada.id]
    entradas.append(nueva)

    escribir_json(proyecto, tipo_archivo, entradas)


def actualizar_entrada_json(proyecto: str, tipo_archivo: str, entrada_id: str, campos: dict):
    """Actualiza campos específicos de una entrada en JSON."""
    entradas = leer_json(proyecto, tipo_archivo)
    for e in entradas:
        if e.get("id") == entrada_id:
            e.update(campos)
            break
    escribir_json(proyecto, tipo_archivo, entradas)


def eliminar_entrada_json(proyecto: str, tipo_archivo: str, entrada_id: str):
    """Elimina una entrada del archivo JSON."""
    entradas = leer_json(proyecto, tipo_archivo)
    entradas = [e for e in entradas if e.get("id") != entrada_id]
    escribir_json(proyecto, tipo_archivo, entradas)


def sincronizar_desde_md(proyecto: str, tipo_archivo: str):
    """Genera/actualiza el .json a partir del .md (fuente de verdad).

    Lee el .md, parsea las entradas, y escribe el .json.
    """
    from .almacenamiento import leer_archivo

    contenido_md = leer_archivo(proyecto, tipo_archivo)
    if not contenido_md:
        # Si el .md está vacío, crear JSON vacío
        escribir_json(proyecto, tipo_archivo, [])
        return

    entradas = parsear_archivo(contenido_md, proyecto)
    dicts = [entrada_a_dict(e) for e in entradas]
    escribir_json(proyecto, tipo_archivo, dicts)


def sincronizar_todos(proyecto: str):
    """Sincroniza todos los archivos .md → .json de un proyecto."""
    from .almacenamiento import ARCHIVOS_ESTANDAR

    for tipo in ARCHIVOS_ESTANDAR:
        sincronizar_desde_md(proyecto, tipo)


def estadisticas_json(proyecto: str) -> dict:
    """Estadísticas del almacenamiento JSON de un proyecto."""
    stats = {}
    for tipo in ARCHIVOS_JSON:
        entradas = leer_json(proyecto, tipo)
        stats[tipo] = len(entradas)
    return stats
