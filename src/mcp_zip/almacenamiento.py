"""Almacenamiento de archivos .md y gestión de proyectos."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .configuracion import config
from .formateador import Entrada, parsear_archivo


# Nombres de archivos estándar
ARCHIVOS_ESTANDAR = {
    "resumen": "RESUMEN.md",
    "errores": "errores.md",
    "decisiones": "decisiones.md",
    "implementacion": "implementacion.md",
    "plan": "plan.md",
}


def crear_proyecto(nombre: str, stack: str = "") -> Path:
    """Crea la estructura de un proyecto nuevo."""
    proyecto_dir = config.proyecto_dir(nombre)
    proyecto_dir.mkdir(parents=True, exist_ok=True)

    # Crear bóveda
    boveda_dir = config.boveda_dir(nombre)
    boveda_dir.mkdir(exist_ok=True)

    # Crear archivos template
    for archivo in ARCHIVOS_ESTANDAR.values():
        filepath = proyecto_dir / archivo
        if not filepath.exists():
            filepath.touch()

    # Crear RESUMEN.md con contenido inicial
    resumen_path = proyecto_dir / "RESUMEN.md"
    if resumen_path.stat().st_size == 0:
        contenido = f"# {nombre.upper()} — Resumen\n\n"
        if stack:
            contenido += f"stack: {stack}\n\n"
        contenido += "## Estado\nsprint: 1 | iniciado | " + datetime.now().strftime("%Y-%m-%d") + "\n"
        resumen_path.write_text(contenido, encoding=config.encoding)

    return proyecto_dir


def proyecto_existe(nombre: str) -> bool:
    """Verifica si un proyecto existe."""
    return config.proyecto_dir(nombre).exists()


def listar_proyectos() -> list[dict]:
    """Lista todos los proyectos con información básica."""
    proyectos = []

    if not config.proyectos_dir.exists():
        return proyectos

    for item in sorted(config.proyectos_dir.iterdir()):
        if item.is_dir():
            # Contar archivos .md
            archivos_md = list(item.glob("*.md"))
            total_lineas = 0
            for f in archivos_md:
                total_lineas += len(f.read_text(encoding=config.encoding).splitlines())

            proyectos.append({
                "nombre": item.name,
                "archivos": len(archivos_md),
                "lineas": total_lineas,
                "tiene_boveda": (item / "boveda").exists(),
                "tiene_db": (item / "memoria.db").exists(),
            })

    return proyectos


def leer_archivo(nombre: str, tipo_archivo: str) -> str:
    """Lee un archivo de memoria de un proyecto."""
    if tipo_archivo in ARCHIVOS_ESTANDAR:
        filename = ARCHIVOS_ESTANDAR[tipo_archivo]
    else:
        filename = tipo_archivo

    filepath = config.proyecto_dir(nombre) / filename
    if not filepath.exists():
        return ""

    return filepath.read_text(encoding=config.encoding)


def escribir_archivo(nombre: str, tipo_archivo: str, contenido: str) -> Path:
    """Escribe contenido en un archivo de memoria."""
    if tipo_archivo in ARCHIVOS_ESTANDAR:
        filename = ARCHIVOS_ESTANDAR[tipo_archivo]
    else:
        filename = tipo_archivo

    filepath = config.proyecto_dir(nombre) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Si el archivo existe, agregar al final
    if filepath.exists() and filepath.stat().st_size > 0:
        existing = filepath.read_text(encoding=config.encoding)
        if not existing.endswith('\n'):
            existing += '\n'
        contenido = existing + '\n' + contenido

    filepath.write_text(contenido, encoding=config.encoding)
    return filepath


def agregar_entrada(nombre: str, tipo_archivo: str, entrada: Entrada) -> Path:
    """Agrega una entrada formateada a un archivo .md + .json."""
    if tipo_archivo in ARCHIVOS_ESTANDAR:
        filename = ARCHIVOS_ESTANDAR[tipo_archivo]
    else:
        filename = tipo_archivo

    filepath = config.proyecto_dir(nombre) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    linea_entrada = entrada.a_linea_compacta()

    if filepath.exists() and filepath.stat().st_size > 0:
        existing = filepath.read_text(encoding=config.encoding)
        if not existing.endswith('\n'):
            existing += '\n'
        contenido = existing + '\n' + linea_entrada + '\n'
    else:
        # Crear con header
        contenido = f"# {tipo_archivo.upper()} — {nombre}\n\n{linea_entrada}\n"

    filepath.write_text(contenido, encoding=config.encoding)

    # Sincronizar JSON secundario
    from .almacenamiento_json import agregar_entrada_json
    agregar_entrada_json(nombre, tipo_archivo, entrada)

    return filepath


def leer_entradas(nombre: str, tipo_archivo: str) -> list[Entrada]:
    """Lee y parsea todas las entradas de un archivo."""
    contenido = leer_archivo(nombre, tipo_archivo)
    if not contenido:
        return []
    return parsear_archivo(contenido, nombre)


def mover_a_boveda(nombre: str, tipo_archivo: str, entrada_id: str) -> bool:
    """Mueve una entrada a la bóveda."""
    entradas = leer_entradas(nombre, tipo_archivo)
    entrada_obj = None
    otras_entradas = []

    for e in entradas:
        if e.id == entrada_id:
            entrada_obj = e
        else:
            otras_entradas.append(e)

    if not entrada_obj:
        return False

    # Marcar como archivada
    entrada_obj.archivado = True
    entrada_obj.fecha_archivado = datetime.now().strftime(config.formato_fecha)

    # Actualizar SQLite para que la búsqueda refleje el archivado
    _actualizar_archivado_sqlite(nombre, entrada_id, True, entrada_obj.fecha_archivado)

    # Escribir en bóveda
    mes = datetime.now().strftime("%Y-%m")
    boveda_filename = f"{tipo_archivo}-{mes}.md"
    boveda_path = config.boveda_dir(nombre) / boveda_filename

    if boveda_path.exists():
        existing = boveda_path.read_text(encoding=config.encoding)
        if not existing.endswith('\n'):
            existing += '\n'
        contenido = existing + '\n' + entrada_obj.a_linea_compacta() + '\n'
    else:
        contenido = f"# {tipo_archivo.upper()} — {nombre} (Bóveda {mes})\n\n{entrada_obj.a_linea_compacta()}\n"

    boveda_path.write_text(contenido, encoding=config.encoding)

    # Reescribir archivo original sin la entrada archivada
    if otras_entradas:
        archivocontenido = f"# {tipo_archivo.upper()} — {nombre}\n\n"
        for e in otras_entradas:
            archivocontenido += e.a_linea_compacta() + '\n\n'
    else:
        archivocontenido = f"# {tipo_archivo.upper()} — {nombre}\n\n"

    filepath = config.proyecto_dir(nombre) / ARCHIVOS_ESTANDAR.get(tipo_archivo, tipo_archivo)
    filepath.write_text(archivocontenido, encoding=config.encoding)

    # Sincronizar JSON: eliminar entrada del JSON activo
    from .almacenamiento_json import eliminar_entrada_json, agregar_entrada_json, entrada_a_dict
    eliminar_entrada_json(nombre, tipo_archivo, entrada_id)

    # Agregar a JSON de bóveda
    boveda_json = f"{tipo_archivo}-{mes}.json"
    boveda_json_path = config.boveda_dir(nombre) / boveda_json
    entradas_boveda = []
    if boveda_json_path.exists():
        try:
            entradas_boveda = json.loads(boveda_json_path.read_text(encoding=config.encoding))
        except (json.JSONDecodeError, TypeError):
            pass
    entradas_boveda.append(entrada_a_dict(entrada_obj))
    boveda_json_path.write_text(
        json.dumps(entradas_boveda, ensure_ascii=False, indent=2),
        encoding=config.encoding,
    )


def _actualizar_archivado_sqlite(nombre: str, entrada_id: str, archivado: bool, fecha_archivado: str):
    """Actualiza el estado de archivado en SQLite."""
    import sqlite3
    db_path = config.db_path(nombre)
    if not db_path.exists():
        return
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "UPDATE entradas SET archivado = ?, fecha_archivado = ? WHERE id = ?",
            (1 if archivado else 0, fecha_archivado, entrada_id),
        )

    return True
