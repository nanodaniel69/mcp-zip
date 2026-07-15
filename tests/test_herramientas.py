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
    configuracion.config.proyectos_dir.mkdir(parents=True, exist_ok=True)
    yield


def test_memoria_iniciar():
    """Test creación de proyecto."""
    resultado = memoria_iniciar("test-proyecto", "Next.js + Prisma")
    assert "✅" in resultado
    assert "test-proyecto" in resultado


def test_memoria_iniciar_duplicado():
    """Test que iniciar proyecto existente activa auto-archivado."""
    memoria_iniciar("test-proyecto")
    resultado = memoria_iniciar("test-proyecto")
    assert "✅" in resultado
    assert "activo" in resultado


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


def test_contenido_con_espacios_se_preserva():
    """Test que contenido con espacios sobrevive al ciclo indexar→buscar."""
    memoria_iniciar("test-espacios")
    memoria_escribir(
        nombre="test-espacios",
        tipo="bug",
        titulo="Color detection falla",
        contexto="Pinturas Tekbond y Miura se fusionan al detectar",
        causa_raiz="paso 8 parser FGP, result.attributes sobreescribe",
        solucion="Cambiar a spread de attributes en parser FGP",
        etiquetas="parser,fgp,colores,pinturas",
    )

    # Buscar por contenido que tiene espacios
    resultado = memoria_buscar("test-espacios", "Tekbond")
    assert "Tekbond" in resultado

    # Buscar por causa raíz
    resultado2 = memoria_buscar("test-espacios", "sobreescribe")
    assert "sobreescribe" in resultado2

    # Verificar que el contexto completo se preserva
    resultado3 = memoria_buscar("test-espacios", "fusionan detectar")
    assert "fusionan" in resultado3


def test_contenido_multiples_campos():
    """Test que múltiples campos de contenido se preservan correctamente."""
    memoria_iniciar("test-multi")
    memoria_escribir(
        nombre="test-multi",
        tipo="decision",
        titulo="Usar SQLite como store",
        contexto="Necesitamos búsqueda rápida",
        decision="SQLite FTS5",
        rationale="Viene con Python, zero dependencias",
        impacto="Reduce tokens en 98%",
        etiquetas="sqlite,busqueda,optimizacion",
    )

    # Verificar que todos los campos son buscables
    for termino in ["rápida", "FTS5", "dependencias", "98%"]:
        resultado = memoria_buscar("test-multi", termino)
        assert termino in resultado, f"No se encontró '{termino}' en resultados"


def test_boveda_sincroniza_con_sqlite():
    """Test que archivar sincroniza SQLite con los .md."""
    memoria_iniciar("test-boveda")
    memoria_escribir(
        nombre="test-boveda",
        tipo="bug",
        titulo="Login falla con SSO",
        contexto="Active Directory integration broken",
        solucion="Fixed LDAP bind call",
        etiquetas="auth,ldap,sso",
        estado="resuelto",
    )

    # Antes de archivar: buscar solo activos lo encuentra
    r1 = memoria_buscar("test-boveda", "LDAP", solo_activos=True)
    assert "LDAP" in r1

    # Archivar (dias=0 para archivar todo resuelto)
    from mcp_zip.herramientas import memoria_archivar
    memoria_archivar("test-boveda", dias=0)

    # Después de archivar: solo activos NO lo encuentra
    r2 = memoria_buscar("test-boveda", "LDAP", solo_activos=True)
    assert "Login falla" not in r2, f"Bug bóveda: entrada archivada aparece en solo_activos: {r2}"

    # Sin filtro: sigue encontrándolo (en la bóveda)
    r3 = memoria_buscar("test-boveda", "LDAP")
    assert "LDAP" in r3
