"""Importador de archivos .md existentes al sistema mcp-zip."""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from .configuracion import config
from .formateador import Entrada
from .almacenamiento import crear_proyecto, agregar_entrada
from .motor import MotorBusqueda


def importar_desde_contexto(nombre: str, ruta_contexto: str) -> dict:
    """Importa archivos .md desde una carpeta context/ existente.

    Args:
        nombre: Nombre del proyecto
        ruta_contexto: Ruta a la carpeta context/ (ej: /home/user/proyecto/context/)

    Returns:
        dict con estadísticas de importación
    """
    ruta = Path(ruta_contexto)
    if not ruta.exists():
        return {"error": f"Ruta no encontrada: {ruta_contexto}"}

    # Crear proyecto si no existe
    crear_proyecto(nombre)

    stats = {
        "archivos_importados": 0,
        "entradas_importadas": 0,
        "errores": [],
    }

    # Mapeo de nombres de archivo a tipos
    mapeo_archivos = {
        "MEMORY.md": "resumen",
        "bugs.md": "errores",
        "decisiones_tecnicas.md": "decisiones",
        "implementacion.md": "implementacion",
        "planificacion.md": "plan",
        "plan-pos-detallado.md": "plan",
    }

    motor = MotorBusqueda(nombre)

    for archivo in ruta.glob("*.md"):
        tipo_archivo = mapeo_archivos.get(archivo.name, archivo.stem)

        try:
            contenido = archivo.read_text(encoding="utf-8")
            entradas = _parsear_archivo_legacy(contenido, tipo_archivo, nombre)

            for entrada in entradas:
                agregar_entrada(nombre, tipo_archivo, entrada)
                motor.indexar_entrada(entrada)
                stats["entradas_importadas"] += 1

            stats["archivos_importados"] += 1

        except Exception as e:
            stats["errores"].append(f"Error importando {archivo.name}: {str(e)}")

    # Sincronizar JSON final para todos los tipos importados
    from .almacenamiento_json import sincronizar_todos
    sincronizar_todos(nombre)

    return stats


def _parsear_archivo_legacy(contenido: str, tipo_archivo: str, proyecto: str) -> list[Entrada]:
    """Parsea un archivo .md en formato legacy a entradas estructuradas."""
    entradas = []

    # Dividir por headers ## o ###
    secciones = re.split(r'\n(?=##\s)', contenido)

    for seccion in secciones:
        seccion = seccion.strip()
        if not seccion.startswith('##'):
            continue

        entrada = _parsear_seccion_legacy(seccion, tipo_archivo, proyecto)
        if entrada:
            entradas.append(entrada)

    return entradas


def _parsear_seccion_legacy(seccion: str, tipo_archivo: str, proyecto: str) -> Optional[Entrada]:
    """Parsea una sección legacy a entrada estructurada."""
    lineas = seccion.split('\n')
    header = lineas[0].strip()

    # Extraer fecha del header: ## [2026-07-14] Bug: Título
    fecha_match = re.search(r'\[(\d{4}-\d{2}-\d{2})\]', header)
    fecha = fecha_match.group(1) if fecha_match else datetime.now().strftime("%Y-%m-%d")

    # Extraer título
    titulo_match = re.search(r'(?:Bug|Decisión|Feature|Implementación):\s*(.+?)(?:\s+[🔴🟢🟡]|$)', header)
    titulo = titulo_match.group(1).strip() if titulo_match else header.replace('##', '').strip()

    # Extraer estado
    estado = "activo"
    if "🟢" in header or "Resuelto" in header or "resuelto" in header:
        estado = "resuelto"
    elif "🔴" in header:
        estado = "activo"
    elif "🟡" in header:
        estado = "pendiente"
    elif "✅" in header:
        estado = "resuelto"

    # Mapear tipo de archivo a tipo de entrada
    tipo_map = {
        "resumen": "resumen",
        "errores": "bug",
        "decisiones": "decision",
        "implementacion": "implementacion",
        "plan": "plan",
    }
    tipo = tipo_map.get(tipo_archivo, tipo_archivo)

    # Parsear contenido (campos - **Campo**: valor)
    contenido = {}
    etiquetas = []

    for linea in lineas[1:]:
        linea = linea.strip()
        if not linea:
            continue

        # Campo legacy: - **Contexto**: valor
        campo_match = re.match(r'^-\s*\*\*(.+?)\*\*:\s*(.+)$', linea)
        if campo_match:
            clave_legacy = campo_match.group(1).lower()
            valor = campo_match.group(2).strip()

            # Mapear claves legacy a compactas
            clave_map = {
                "contexto": "ctx",
                "causa raíz": "root",
                "causa raiz": "root",
                "solución": "fix",
                "solucion": "fix",
                "decisión tomada": "decision",
                "decision tomada": "decision",
                "rationale": "rationale",
                "archivos afectados": "files",
                "impacto": "impact",
                "estado": "estado",
            }
            clave = clave_map.get(clave_legacy, clave_legacy)

            if clave == "estado":
                if "resuelto" in valor.lower():
                    estado = "resuelto"
                elif "activo" in valor.lower():
                    estado = "activo"
            elif clave == "files":
                archivos = [f.strip() for f in valor.split(',') if f.strip()]
                continue
            else:
                contenido[clave] = valor

    return Entrada(
        tipo=tipo,
        titulo=titulo,
        fecha=fecha,
        estado=estado,
        contenido=contenido,
        etiquetas=etiquetas,
        proyecto=proyecto,
    )
