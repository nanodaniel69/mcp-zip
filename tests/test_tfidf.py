"""Tests para el motor TF-IDF."""

import pytest
from mcp_zip.tfidf import (
    tokenizar,
    calcular_tf,
    calcular_idf,
    calcular_tfidf,
    similitud_coseno,
    MotorTFIDF,
    texto_entrada_compacto,
)


def test_tokenizar_basico():
    """Test tokenización básica."""
    tokens = tokenizar("Hola mundo cruel")
    assert "hola" in tokens
    assert "mundo" in tokens
    assert "cruel" in tokens


def test_tokenizar_remueve_stop_words():
    """Test que stop words se eliminan."""
    tokens = tokenizar("el gato está en la casa")
    assert "el" not in tokens
    assert "la" not in tokens
    assert "en" not in tokens
    assert "gato" in tokens
    assert "casa" in tokens


def test_tokenizar_minusculas():
    """Test normalización a minúsculas."""
    tokens = tokenizar("SQLite FTS5 es RÁPIDO")
    assert "sqlite" in tokens
    assert "fts5" in tokens
    assert "rápido" in tokens


def test_tokenizar_puntuacion():
    """Test remoción de puntuación."""
    tokens = tokenizar("bug-fix: parser.fgp.ts falla!")
    assert "bug" in tokens
    assert "fix" in tokens
    assert "parser" in tokens
    assert "fgp" in tokens
    assert "ts" in tokens  # 2 chars, pasa filtro
    assert "!" not in tokens  # puntuación removida
    assert "falla" in tokens


def test_calcular_tf():
    """Test Term Frequency."""
    tokens = ["bug", "parser", "bug", "fgp", "bug"]
    tf = calcular_tf(tokens)
    assert tf["bug"] == 1.0  # max freq
    assert tf["parser"] == pytest.approx(1 / 3, abs=0.01)


def test_calcular_idf():
    """Test Inverse Document Frequency."""
    documentos = [
        ["bug", "parser"],
        ["bug", "fgp"],
        ["decision", "arquitectura"],
    ]
    idf = calcular_idf(documentos)

    # "bug" aparece en 2/3 docs → IDF bajo
    # "parser" aparece en 1/3 docs → IDF alto
    assert idf["bug"] < idf["parser"]


def test_similitud_coseno():
    """Test similitud coseno."""
    vec_a = {"bug": 1.0, "parser": 0.5}
    vec_b = {"bug": 1.0, "parser": 0.5}
    vec_c = {"decision": 1.0, "arquitectura": 0.5}

    # Mismos vectores → similitud 1.0
    assert similitud_coseno(vec_a, vec_b) == pytest.approx(1.0, abs=0.01)

    # Vectores diferentes → similitud baja
    assert similitud_coseno(vec_a, vec_c) == pytest.approx(0.0, abs=0.01)


def test_motor_tfidf_rerankear():
    """Test re-ranking con TF-IDF."""
    motor = MotorTFIDF()

    # Construir índice con 3 entradas
    motor.construir_idf([
        "bug parser color detection falla",
        "decisión arquitectura microservicios",
        "bug parser FGP tokenización rota",
    ])

    # Buscar "parser bug" → debería rankear entradas 0 y 2 arriba
    entradas = [
        ("e1", "bug parser color detection falla", 1.0),
        ("e2", "decisión arquitectura microservicios", 0.5),
        ("e3", "bug parser FGP tokenización rota", 1.0),
    ]

    resultados = motor.rerankear("parser bug", entradas)
    ids_orden = [eid for eid, _ in resultados]

    # Las entradas con "parser" y "bug" deben estar arriba
    assert ids_orden[0] in ("e1", "e3")
    assert ids_orden[-1] == "e2"  # La de arquitectura abajo


def test_motor_tfidf_score_bajo_para_no_relacionadas():
    """Test que TF-IDF da score bajo a entradas no relacionadas."""
    motor = MotorTFIDF()
    motor.construir_idf([
        "bug parser color detection",
        "decisión usar React para frontend",
    ])

    # Buscar "parser" en una entrada que no lo menciona
    score = motor.score_tfidf("parser", "decisión usar React para frontend")
    assert score < 0.1


def test_texto_entrada_compacto():
    """Test extracción de texto plano."""
    texto = texto_entrada_compacto({
        "titulo": "Bug en parser",
        "contenido": {"ctx": "Falla al parsear JSON", "fix": "Usar try-catch"},
        "etiquetas": ["parser", "json", "error"],
    })

    assert "Bug en parser" in texto
    assert "ctx Falla al parsear JSON" in texto
    assert "parser" in texto
    assert "json" in texto


def test_texto_entrada_compacto_vacio():
    """Test con entrada vacía."""
    texto = texto_entrada_compacto({})
    assert texto == ""
