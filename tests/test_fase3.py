"""Tests para Fase 3: estadísticas, sincronización, .mcp-zip."""

import pytest
import tempfile
from pathlib import Path
from mcp_zip import configuracion
from mcp_zip.herramientas import (
    memoria_iniciar,
    memoria_escribir,
    memoria_buscar,
    memoria_estadisticas,
    memoria_sincronizar,
    memoria_exportar_zip,
    memoria_importar_zip,
    memoria_listar_zip,
)


@pytest.fixture(autouse=True)
def setup_temp_dir(tmp_path):
    """Configura un directorio temporal para cada test."""
    configuracion.config.root = tmp_path / ".memoria"
    configuracion.config.proyectos_dir.mkdir(parents=True, exist_ok=True)
    yield


# ==================== memoria_estadisticas ====================

def test_estadisticas_proyecto_vacio():
    """Test estadísticas de proyecto sin entradas."""
    memoria_iniciar("test-stats")
    resultado = memoria_estadisticas("test-stats")
    assert "📊" in resultado
    assert "test-stats" in resultado
    assert "Total: 0" in resultado


def test_estadisticas_con_entradas():
    """Test estadísticas con entradas."""
    memoria_iniciar("test-stats")
    memoria_escribir(
        nombre="test-stats",
        tipo="bug",
        titulo="Bug test",
        contexto="Contexto de prueba",
        etiquetas="test",
    )
    memoria_escribir(
        nombre="test-stats",
        tipo="decision",
        titulo="Decisión test",
        decision="Usar SQLite",
        etiquetas="sqlite",
    )
    resultado = memoria_estadisticas("test-stats")
    assert "Total: 2" in resultado
    assert "bug" in resultado
    assert "decision" in resultado


def test_estadisticas_proyecto_no_existe():
    """Test error con proyecto inexistente."""
    resultado = memoria_estadisticas("no-existe")
    assert "❌" in resultado


# ==================== memoria_sincronizar ====================

def test_sincronizar_proyectos():
    """Test sincronización de todos los proyectos."""
    memoria_iniciar("sync-1")
    memoria_escribir(
        nombre="sync-1",
        tipo="bug",
        titulo="Bug sync 1",
        contexto="Test",
    )
    memoria_iniciar("sync-2")
    memoria_escribir(
        nombre="sync-2",
        tipo="decision",
        titulo="Decisión sync 2",
        decision="Test",
    )

    resultado = memoria_sincronizar()
    assert "🔄" in resultado
    assert "sync-1" in resultado
    assert "sync-2" in resultado
    assert "✅" in resultado


def test_sincronizar_sin_proyectos():
    """Test sincronización sin proyectos."""
    resultado = memoria_sincronizar()
    assert "No hay proyectos" in resultado


# ==================== .mcp-zip ====================

def test_exportar_zip():
    """Test exportación a .mcp-zip."""
    memoria_iniciar("test-zip")
    memoria_escribir(
        nombre="test-zip",
        tipo="bug",
        titulo="Bug zip",
        contexto="Test export",
        etiquetas="zip,test",
    )

    resultado = memoria_exportar_zip("test-zip")
    assert "📦" in resultado
    assert "test-zip.mcp-zip" in resultado

    # Verificar que el archivo existe
    zip_path = configuracion.config.proyectos_dir / "test-zip.mcp-zip"
    assert zip_path.exists()


def test_exportar_zip_proyecto_no_existe():
    """Test error al exportar proyecto inexistente."""
    resultado = memoria_exportar_zip("no-existe")
    assert "❌" in resultado


def test_importar_zip():
    """Test importación desde .mcp-zip."""
    # Primero exportar
    memoria_iniciar("origen")
    memoria_escribir(
        nombre="origen",
        tipo="bug",
        titulo="Bug origen",
        contexto="Dato a importar",
    )
    memoria_exportar_zip("origen")

    # Limpiar directorio de destino
    import shutil
    destino_dir = configuracion.config.proyectos_dir / "destino"
    if destino_dir.exists():
        shutil.rmtree(destino_dir)

    # Importar
    zip_path = configuracion.config.proyectos_dir / "origen.mcp-zip"
    resultado = memoria_importar_zip(str(zip_path))
    assert "📥" in resultado
    assert "origen" in resultado

    # Verificar que se puede buscar
    r = memoria_buscar("origen", "Bug origen")
    assert "Bug origen" in r


def test_importar_zip_archivo_no_existe():
    """Test error al importar archivo inexistente."""
    resultado = memoria_importar_zip("/tmp/no-existe.mcp-zip")
    assert "❌" in resultado


def test_listar_zip():
    """Test listado de contenido .mcp-zip."""
    memoria_iniciar("test-listar")
    memoria_escribir(
        nombre="test-listar",
        tipo="bug",
        titulo="Bug listar",
        contexto="Test",
    )
    memoria_exportar_zip("test-listar")

    zip_path = configuracion.config.proyectos_dir / "test-listar.mcp-zip"
    resultado = memoria_listar_zip(str(zip_path))
    assert "📋" in resultado
    assert "test-listar" in resultado
    assert ".md" in resultado
    assert ".json" in resultado


def test_roundtrip_export_import():
    """Test roundtrip completo: crear → exportar → importar → buscar."""
    # Crear
    memoria_iniciar("roundtrip")
    memoria_escribir(
        nombre="roundtrip",
        tipo="bug",
        titulo="Parser FGP falla",
        contexto="Error en paso 8",
        solucion="Usar spread",
        etiquetas="parser,fgp",
    )
    memoria_escribir(
        nombre="roundtrip",
        tipo="decision",
        titulo="Usar TF-IDF",
        decision="Búsqueda semántica ligera",
        etiquetas="tfidf,busqueda",
    )

    # Exportar
    memoria_exportar_zip("roundtrip")

    # Limpiar y reimportar
    import shutil
    project_dir = configuracion.config.proyecto_dir("roundtrip")
    if project_dir.exists():
        shutil.rmtree(project_dir)

    zip_path = configuracion.config.proyectos_dir / "roundtrip.mcp-zip"
    memoria_importar_zip(str(zip_path))

    # Verificar búsquedas
    r1 = memoria_buscar("roundtrip", "parser")
    assert "Parser FGP falla" in r1

    r2 = memoria_buscar("roundtrip", "TF-IDF")
    assert "Usar TF-IDF" in r2
