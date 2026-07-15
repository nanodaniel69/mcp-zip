"""Tests para el almacenamiento JSON secundario."""

import pytest
import tempfile
from pathlib import Path
from mcp_zip import configuracion
from mcp_zip.formateador import Entrada
from mcp_zip.almacenamiento import crear_proyecto, agregar_entrada
from mcp_zip.almacenamiento_json import (
    leer_json,
    escribir_json,
    entrada_a_dict,
    dict_a_entrada,
    agregar_entrada_json,
    sincronizar_desde_md,
    sincronizar_todos,
    estadisticas_json,
)


@pytest.fixture(autouse=True)
def setup_temp_dir(tmp_path):
    """Configura un directorio temporal para cada test."""
    configuracion.config.root = tmp_path / ".memoria"
    configuracion.config.proyectos_dir.mkdir(parents=True, exist_ok=True)
    yield


def test_entrada_a_dict():
    """Test conversión Entrada → dict."""
    entrada = Entrada(
        tipo="bug",
        titulo="Test bug",
        estado="activo",
        contenido={"ctx": "Contexto de prueba"},
        etiquetas=["test", "bug"],
    )
    d = entrada_a_dict(entrada)
    assert d["tipo"] == "bug"
    assert d["titulo"] == "Test bug"
    assert d["contenido"]["ctx"] == "Contexto de prueba"
    assert d["etiquetas"] == ["test", "bug"]
    assert d["id"] != ""


def test_dict_a_entrada():
    """Test conversión dict → Entrada."""
    d = {
        "id": "bug-2026-07-15-test",
        "tipo": "bug",
        "titulo": "Test bug",
        "fecha": "2026-07-15",
        "estado": "resuelto",
        "contenido": {"ctx": "Contexto", "fix": "Solución"},
        "etiquetas": ["test"],
        "archivos_afectados": ["src/test.ts"],
        "proyecto": "ferreteria",
        "archivado": False,
        "fecha_archivado": "",
    }
    entrada = dict_a_entrada(d)
    assert entrada.id == "bug-2026-07-15-test"
    assert entrada.tipo == "bug"
    assert entrada.contenido["fix"] == "Solución"
    assert entrada.etiquetas == ["test"]


def test_escribir_leer_json():
    """Test escribir y leer JSON."""
    crear_proyecto("test-json")
    entradas = [
        {"id": "bug-1", "tipo": "bug", "titulo": "Bug 1"},
        {"id": "bug-2", "tipo": "bug", "titulo": "Bug 2"},
    ]
    escribir_json("test-json", "errores", entradas)
    leidas = leer_json("test-json", "errores")
    assert len(leidas) == 2
    assert leidas[0]["titulo"] == "Bug 1"
    assert leidas[1]["titulo"] == "Bug 2"


def test_agregar_entrada_json():
    """Test agregar entrada al JSON."""
    crear_proyecto("test-json")
    entrada = Entrada(
        tipo="bug",
        titulo="Bug nuevo",
        contenido={"ctx": "Contexto"},
        etiquetas=["nuevo"],
    )
    agregar_entrada_json("test-json", "errores", entrada)
    leidas = leer_json("test-json", "errores")
    assert len(leidas) == 1
    assert leidas[0]["titulo"] == "Bug nuevo"
    assert leidas[0]["contenido"]["ctx"] == "Contexto"


def test_agregar_entrada_json_reemplaza_duplicado():
    """Test que agregar entrada duplicada reemplaza la anterior."""
    crear_proyecto("test-json")
    entrada1 = Entrada(
        id="bug-dup",
        tipo="bug",
        titulo="Bug viejo",
        contenido={"ctx": "Viejo"},
    )
    entrada2 = Entrada(
        id="bug-dup",
        tipo="bug",
        titulo="Bug nuevo",
        contenido={"ctx": "Nuevo"},
    )
    agregar_entrada_json("test-json", "errores", entrada1)
    agregar_entrada_json("test-json", "errores", entrada2)
    leidas = leer_json("test-json", "errores")
    assert len(leidas) == 1
    assert leidas[0]["titulo"] == "Bug nuevo"


def test_sincronizar_desde_md():
    """Test sincronizar JSON desde .md."""
    crear_proyecto("test-sync")
    entrada = Entrada(
        tipo="bug",
        titulo="Sync test",
        contenido={"ctx": "Desde .md"},
        etiquetas=["sync"],
    )
    agregar_entrada("test-sync", "errores", entrada)

    # Verificar que el JSON se creó automáticamente
    leidas = leer_json("test-sync", "errores")
    assert len(leidas) == 1
    assert leidas[0]["titulo"] == "Sync test"


def test_sincronizar_todos():
    """Test sincronizar todos los .md → .json."""
    crear_proyecto("test-sync-all")
    for tipo in ["bug", "decision", "plan"]:
        entrada = Entrada(
            tipo=tipo,
            titulo=f"Test {tipo}",
            contenido={"ctx": f"Contexto {tipo}"},
        )
        agregar_entrada("test-sync-all", tipo if tipo != "bug" else "errores", entrada)

    stats = estadisticas_json("test-sync-all")
    assert stats["errores"] >= 1


def test_estadisticas_json():
    """Test estadísticas del JSON."""
    crear_proyecto("test-stats")
    for i in range(3):
        entrada = Entrada(
            tipo="bug",
            titulo=f"Bug {i}",
            contenido={"ctx": f"Contexto {i}"},
        )
        agregar_entrada_json("test-stats", "errores", entrada)

    stats = estadisticas_json("test-stats")
    assert stats["errores"] == 3
    assert stats["decisiones"] == 0


def test_json_contenido_con_espacios():
    """Test que contenido con espacios se preserva en JSON."""
    crear_proyecto("test-json-espacios")
    entrada = Entrada(
        tipo="bug",
        titulo="Color detection falla",
        contenido={
            "ctx": "Pinturas Tekbond y Miura se fusionan al detectar color",
            "root": "paso 8 parser FGP sobreescribe objeto",
            "fix": "Cambiar a spread de attributes",
        },
        etiquetas=["parser", "fgp", "colores"],
    )
    agregar_entrada_json("test-json-espacios", "errores", entrada)
    leidas = leer_json("test-json-espacios", "errores")
    assert leidas[0]["contenido"]["ctx"] == "Pinturas Tekbond y Miura se fusionan al detectar color"
    assert leidas[0]["contenido"]["root"] == "paso 8 parser FGP sobreescribe objeto"


def test_json_archivado():
    """Test que estado archivado se sincroniza en JSON."""
    crear_proyecto("test-json-arch")
    entrada = Entrada(
        id="bug-arch",
        tipo="bug",
        titulo="Bug archivado",
        estado="resuelto",
    )
    agregar_entrada_json("test-json-arch", "errores", entrada)

    # Simular archivado
    from mcp_zip.almacenamiento_json import actualizar_entrada_json
    actualizar_entrada_json("test-json-arch", "errores", "bug-arch", {
        "archivado": True,
        "fecha_archivado": "2026-07-15",
    })

    leidas = leer_json("test-json-arch", "errores")
    assert leidas[0]["archivado"] is True
    assert leidas[0]["fecha_archivado"] == "2026-07-15"
