"""Motor de búsqueda con SQLite FTS5."""

import sqlite3
import json
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .configuracion import config
from .formateador import Entrada


@dataclass
class ResultadoBusqueda:
    """Resultado de una búsqueda."""
    entrada: Entrada
    score: float
    fuente: str  # "activos" o "boveda"


class MotorBusqueda:
    """Motor de búsqueda con SQLite FTS5."""

    def __init__(self, proyecto: str):
        self.proyecto = proyecto
        self.db_path = config.db_path(proyecto)
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos SQLite con FTS5."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.db_path)) as conn:
            # Tabla de entradas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entradas (
                    id TEXT PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    contenido TEXT,
                    etiquetas TEXT,
                    archivos_afectados TEXT,
                    proyecto TEXT,
                    archivado INTEGER DEFAULT 0,
                    fecha_archivado TEXT
                )
            """)

            # Tabla FTS5 para búsqueda full-text
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS entradas_fts USING fts5(
                    id,
                    tipo,
                    titulo,
                    texto_contenido,
                    etiquetas,
                    content='entradas',
                    content_rowid='rowid'
                )
            """)

            # Triggers para mantener FTS sincronizado
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS entradas_ai AFTER INSERT ON entradas BEGIN
                    INSERT INTO entradas_fts(rowid, id, tipo, titulo, texto_contenido, etiquetas)
                    VALUES (new.rowid, new.id, new.tipo, new.titulo, new.contenido, new.etiquetas);
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS entradas_ad AFTER DELETE ON entradas BEGIN
                    INSERT INTO entradas_fts(entradas_fts, rowid, id, tipo, titulo, texto_contenido, etiquetas)
                    VALUES ('delete', old.rowid, old.id, old.tipo, old.titulo, old.contenido, old.etiquetas);
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS entradas_au AFTER UPDATE ON entradas BEGIN
                    INSERT INTO entradas_fts(entradas_fts, rowid, id, tipo, titulo, texto_contenido, etiquetas)
                    VALUES ('delete', old.rowid, old.id, old.tipo, old.titulo, old.contenido, old.etiquetas);
                    INSERT INTO entradas_fts(rowid, id, tipo, titulo, texto_contenido, etiquetas)
                    VALUES (new.rowid, new.id, new.tipo, new.titulo, new.contenido, new.etiquetas);
                END
            """)

    def indexar_entrada(self, entrada: Entrada):
        """Indexa una entrada en la base de datos."""
        contenido_json = json.dumps(entrada.contenido, ensure_ascii=False)
        etiquetas_str = ','.join(entrada.etiquetas)
        archivos_str = ','.join(entrada.archivos_afectados)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO entradas
                (id, tipo, titulo, fecha, estado, contenido, etiquetas,
                 archivos_afectados, proyecto, archivado, fecha_archivado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entrada.id,
                entrada.tipo,
                entrada.titulo,
                entrada.fecha,
                entrada.estado,
                contenido_json,
                etiquetas_str,
                archivos_str,
                entrada.proyecto,
                1 if entrada.archivado else 0,
                entrada.fecha_archivado,
            ))

    def buscar(self, query: str, solo_activos: bool = False, limite: int = 5) -> list[ResultadoBusqueda]:
        """Busca entradas por texto completo con ranking FTS5."""
        # Limpiar query para FTS5
        query_limpia = re.sub(r'[^\w\s]', ' ', query)
        query_fts = ' OR '.join(query_limpia.split())

        if not query_fts:
            return []

        resultados = []

        with sqlite3.connect(str(self.db_path)) as conn:
            # Buscar en FTS5
            sql = """
                SELECT e.id, e.tipo, e.titulo, e.fecha, e.estado,
                       e.contenido, e.etiquetas, e.archivos_afectados,
                       e.archivado, e.fecha_archivado,
                       rank
                FROM entradas_fts f
                JOIN entradas e ON f.rowid = e.rowid
                WHERE entradas_fts MATCH ?
            """
            params = [query_fts]

            if solo_activos:
                sql += " AND e.archivado = 0"

            sql += " ORDER BY rank LIMIT ?"
            params.append(limite)

            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                # Si FTS5 falla, buscar con LIKE
                sql_like = """
                    SELECT id, tipo, titulo, fecha, estado,
                           contenido, etiquetas, archivos_afectados,
                           archivado, fecha_archivado, 0
                    FROM entradas
                    WHERE titulo LIKE ? OR contenido LIKE ? OR etiquetas LIKE ?
                """
                like_param = f"%{query}%"
                params_like = [like_param, like_param, like_param]

                if solo_activos:
                    sql_like += " AND archivado = 0"

                sql_like += " LIMIT ?"
                params_like.append(limite)

                rows = conn.execute(sql_like, params_like).fetchall()

            for row in rows:
                entrada = Entrada(
                    id=row[0],
                    tipo=row[1],
                    titulo=row[2],
                    fecha=row[3],
                    estado=row[4],
                    contenido=self._parsear_contenido(row[5]),
                    etiquetas=row[6].split(',') if row[6] else [],
                    archivos_afectados=row[7].split(',') if row[7] else [],
                    proyecto=self.proyecto,
                    archivado=bool(row[8]),
                    fecha_archivado=row[9] or "",
                )
                score = abs(row[10]) if row[10] else 0
                fuente = "boveda" if entrada.archivado else "activos"

                resultados.append(ResultadoBusqueda(
                    entrada=entrada,
                    score=score,
                    fuente=fuente,
                ))

        return resultados

    def estadisticas(self) -> dict:
        """Obtiene estadísticas del proyecto."""
        with sqlite3.connect(str(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM entradas").fetchone()[0]
            activos = conn.execute("SELECT COUNT(*) FROM entradas WHERE archivado = 0").fetchone()[0]
            archivados = conn.execute("SELECT COUNT(*) FROM entradas WHERE archivado = 1").fetchone()[0]

            por_tipo = conn.execute(
                "SELECT tipo, COUNT(*) FROM entradas GROUP BY tipo"
            ).fetchall()

            por_estado = conn.execute(
                "SELECT estado, COUNT(*) FROM entradas GROUP BY estado"
            ).fetchall()

        return {
            "total": total,
            "activos": activos,
            "archivados": archivados,
            "por_tipo": {r[0]: r[1] for r in por_tipo},
            "por_estado": {r[0]: r[1] for r in por_estado},
        }

    def _parsear_contenido(self, contenido_str: str) -> dict:
        """Parsea el contenido JSON a diccionario."""
        if not contenido_str:
            return {}
        try:
            return json.loads(contenido_str)
        except (json.JSONDecodeError, TypeError):
            # Fallback: contenido en formato legacy "clave: valor"
            resultado = {}
            for linea in contenido_str.split('\n'):
                linea = linea.strip()
                if ':' in linea:
                    clave, valor = linea.split(':', 1)
                    resultado[clave.strip()] = valor.strip()
            return resultado
