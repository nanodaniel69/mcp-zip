"""Tests para las herramientas MCP."""

import pytest
import tempfile
from pathlib import Path
from mcp_zip import configuracion
from mcp_zip.herramientas import (
    memoria_iniciar,
    memoria_escribir,
    memoria_buscar,
    memoria_leer,
    memoria_resumen,
    memoria_listar,
)


@pytest.fixture(autouse=True)
def setup_temp_dir(tmp_path):
    """Configura un directorio temporal para cada test."""
    configuracion.config.root = tmp_path / ".memoria"
    configuracion.config.proyectos_dir = configuracion.config.root / "proyectos"
    configuracion.config.proyectos_dir.mkdir(parents=True, exist_ok=True)
    yield


def test_memoria_iniciar():
    """Test creación de proyecto."""
    resultado = memoria_iniciar("test-proyecto", "Next.js + Prisma")
    assert "✅" in resultado
    assert "test-proyecto" in resultado


def test_memoria_iniciar_duplicado():
    """Test que no se crea proyecto duplicado."""
    memoria_iniciar("test-proyecto")
    resultado = memoria_iniciar("test-proyecto")
    assert "⚠️" in resultado


def test_memoria_escribir():
    """Test escritura de entrada."""
    memoria_iniciar("test-proyecto")
    resultado = memoria_escribir(
        nombre="test-proyecto",
        tipo="bug",
        titulo="Test bug",
        contexto="Contexto de prueba",
        solucion="Solución de prueba",
        etiquetas="test,bug",
    )
    assert "✅" in resultado


def test_memoria_buscar():
    """Test búsqueda de entradas."""
    memoria_iniciar("test-proyecto")
    memoria_escribir(
        nombre="test-proyecto",
        tipo="bug",
        titulo="Color detection falla",
        contexto="Pinturas se fusionan",
        etiquetas="parser,colores",
    )

    resultado = memoria_buscar("test-proyecto", "color")
    assert "🔍" in resultado
    assert "Color detection" in resultado


def test_memoria_leer():
    """Test lectura de archivo."""
    memoria_iniciar("test-proyecto")
    resultado = memoria_leer("test-proyecto", "resumen")
    assert "test-proyecto" in resultado.upper() or "resumen" in resultado.lower()


def test_memoria_listar():
    """Test listado de proyectos."""
    memoria_iniciar("proyecto-1")
    memoria_iniciar("proyecto-2")
    resultado = memoria_listar()
    assert "proyecto-1" in resultado
    assert "proyecto-2" in resultado
