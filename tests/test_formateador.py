"""Tests para el formateador de entradas."""

import pytest
from mcp_zip.formateador import Entrada, parsear_entrada, parsear_archivo, generar_id


def test_generar_id():
    """Test generación de IDs."""
    id1 = generar_id("bug", "Color detection falla", "2026-07-14")
    assert id1 == "bug-2026-07-14-color-detection-falla"

    id2 = generar_id("decision", "Usar PostgreSQL", "2026-07-14")
    assert id2 == "decision-2026-07-14-usar-postgresql"


def test_entrada_a_linea_compacta():
    """Test conversión de entrada a formato compacto."""
    entrada = Entrada(
        tipo="bug",
        titulo="Color detection falla",
        fecha="2026-07-14",
        estado="resuelto",
        contenido={"ctx": "Pinturas se fusionan", "fix": "Spread attributes"},
        etiquetas=["parser", "fgp"],
        archivos_afectados=["src/parser.ts"],
    )

    linea = entrada.a_linea_compacta()
    assert "### bug | 2026-07-14 | resuelto" in linea
    assert "Color detection falla" in linea
    assert "ctx: Pinturas se fusionan" in linea
    assert "tags: parser,fgp" in linea
    assert "files: src/parser.ts" in linea


def test_parsear_entrada():
    """Test parseo de entrada desde formato compacto."""
    texto = """### bug | 2026-07-14 | resuelto
Color detection falla
ctx: Pinturas se fusionan
fix: Spread attributes
tags: parser,fgp
files: src/parser.ts"""

    entrada = parsear_entrada(texto, "ferreteria")

    assert entrada is not None
    assert entrada.tipo == "bug"
    assert entrada.fecha == "2026-07-14"
    assert entrada.estado == "resuelto"
    assert entrada.titulo == "Color detection falla"
    assert entrada.contenido["ctx"] == "Pinturas se fusionan"
    assert entrada.contenido["fix"] == "Spread attributes"
    assert entrada.etiquetas == ["parser", "fgp"]
    assert entrada.archivos_afectados == ["src/parser.ts"]
    assert entrada.proyecto == "ferreteria"


def test_parsear_archivo():
    """Test parseo de archivo completo con múltiples entradas."""
    texto = """# errores — ferreteria

### bug | 2026-07-14 | resuelto
Color detection falla
ctx: Pinturas se fusionan
fix: Spread attributes
tags: parser,fgp

### bug | 2026-07-13 | activo
PALA PUNTA no funciona
ctx: PUNTA está en PRODUCT_TYPES
tags: parser,fgp"""

    entradas = parsear_archivo(texto, "ferreteria")

    assert len(entradas) == 2
    assert entradas[0].tipo == "bug"
    assert entradas[0].estado == "resuelto"
    assert entradas[1].tipo == "bug"
    assert entradas[1].estado == "activo"


def test_entrada_a_dict():
    """Test conversión de entrada a diccionario."""
    entrada = Entrada(
        tipo="bug",
        titulo="Test",
        fecha="2026-07-14",
        estado="activo",
    )

    d = entrada.a_dict()
    assert d["tipo"] == "bug"
    assert d["titulo"] == "Test"
    assert d["fecha"] == "2026-07-14"
    assert d["estado"] == "activo"
    assert "id" in d
