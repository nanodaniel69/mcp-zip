"""Formateador de entradas de memoria.

Define el formato compacto optimizado para modelos de IA.
"""

import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Entrada:
    """Una entrada de memoria estructurada."""

    id: str = ""
    tipo: str = ""  # bug, decision, implementacion, plan, resumen
    titulo: str = ""
    fecha: str = ""
    estado: str = ""  # activo, resuelto, pendiente, archivado
    contenido: dict = field(default_factory=dict)
    etiquetas: list = field(default_factory=list)
    archivos_afectados: list = field(default_factory=list)
    proyecto: str = ""
    archivado: bool = False
    fecha_archivado: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = self._generar_id()
        if not self.fecha:
            self.fecha = datetime.now().strftime("%Y-%m-%d")

    def _generar_id(self) -> str:
        """Genera un ID único para la entrada."""
        fecha = self.fecha or datetime.now().strftime("%Y-%m-%d")
        tipo = self.tipo or "entrada"
        titulo_corto = re.sub(r'[^a-z0-9]', '-', self.titulo.lower())[:30]
        return f"{tipo}-{fecha}-{titulo_corto}"

    def a_linea_compacta(self) -> str:
        """Convierte la entrada a formato compacto para .md."""
        parts = [f"### {self.tipo} | {self.fecha} | {self.estado}"]
        parts.append(self.titulo)

        for clave, valor in self.contenido.items():
            if valor:
                parts.append(f"{clave}: {valor}")

        if self.etiquetas:
            parts.append(f"tags: {','.join(self.etiquetas)}")

        if self.archivos_afectados:
            parts.append(f"files: {','.join(self.archivos_afectados)}")

        return '\n'.join(parts)

    def a_dict(self) -> dict:
        """Convierte la entrada a diccionario."""
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "fecha": self.fecha,
            "estado": self.estado,
            "contenido": self.contenido,
            "etiquetas": self.etiquetas,
            "archivos_afectados": self.archivos_afectados,
            "proyecto": self.proyecto,
            "archivado": self.archivado,
            "fecha_archivado": self.fecha_archivado,
        }


def parsear_entrada(texto: str, proyecto: str = "") -> Optional[Entrada]:
    """Parsea una entrada desde formato compacto .md.

    Formo esperado:
    ### tipo | fecha | estado
    titulo
    clave: valor
    tags: a,b,c
    files: archivo1,archivo2
    """
    lineas = texto.strip().split('\n')
    if not lineas:
        return None

    # Parsear header: ### tipo | fecha | estado
    header = lineas[0].strip()
    match = re.match(r'^###\s+(\w+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\w+)$', header)
    if not match:
        return None

    tipo, fecha, estado = match.groups()

    # Parsear título (segunda línea)
    titulo = lineas[1].strip() if len(lineas) > 1 else ""

    # Parsear campos clave: valor
    contenido = {}
    etiquetas = []
    archivos = []

    for linea in lineas[2:]:
        linea = linea.strip()
        if not linea:
            continue

        if linea.startswith('tags:'):
            etiquetas = [t.strip() for t in linea[5:].split(',') if t.strip()]
        elif linea.startswith('files:'):
            archivos = [f.strip() for f in linea[6:].split(',') if f.strip()]
        elif ':' in linea:
            clave, valor = linea.split(':', 1)
            contenido[clave.strip()] = valor.strip()

    return Entrada(
        tipo=tipo,
        titulo=titulo,
        fecha=fecha,
        estado=estado,
        contenido=contenido,
        etiquetas=etiquetas,
        archivos_afectados=archivos,
        proyecto=proyecto,
    )


def parsear_archivo(texto: str, proyecto: str = "") -> list[Entrada]:
    """Parsea un archivo .md completo con múltiples entradas."""
    entradas = []

    # Dividir por headers ###
    secciones = re.split(r'\n(?=###\s)', texto)

    for seccion in secciones:
        seccion = seccion.strip()
        if seccion.startswith('###'):
            entrada = parsear_entrada(seccion, proyecto)
            if entrada:
                entradas.append(entrada)

    return entradas


def generar_id(tipo: str, titulo: str, fecha: str = "") -> str:
    """Genera un ID para una entrada."""
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    titulo_corto = re.sub(r'[^a-z0-9]', '-', titulo.lower())[:30]
    return f"{tipo}-{fecha}-{titulo_corto}"
