"""Motor TF-IDF ligero para re-ranking de resultados.

No requiere modelos ML. Pura matemática.
Tokenizer optimizado para español + stop words.
"""

import math
import re
from collections import Counter
from typing import Optional


# Stop words en español (las más comunes)
STOP_WORDS_ES = frozenset({
    "de", "la", "el", "en", "y", "a", "los", "del", "las", "un", "por",
    "con", "no", "una", "su", "para", "es", "al", "lo", "como", "más",
    "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta",
    "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta",
    "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos",
    "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
    "e", "esto", "mi", "antes", "algunos", "qué", "unos", "yo", "otro",
    "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes",
    "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas",
    "algo", "nosotros", "ella", "había", "ser", "tiene", "tiene", "han",
    "era", "cada", "fue", "tiene", "hacer", "he", "dan", "puede", "hoy",
    "va", "van", "vez", "solo", "si", "bien", "aquí", "ahí", "así",
    "ir", "ver", "dar", "deber", "poner", "querer", "llegar", "pasar",
    "deber", "seguir", "parte", "creo", "hay", "vez", "ver", "dos",
    "tres", "cual", "tipo", "manera", "caso", "punto", "tema", "cada",
})

# Stop words en inglés (comunes en contexto técnico)
STOP_WORDS_EN = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "but", "and",
    "or", "if", "while", "about", "against", "it", "its", "this", "that",
    "these", "those", "what", "which", "who", "whom", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her", "they",
    "them", "their", "mine", "yours", "hers", "ours", "theirs",
})

STOP_WORDS = STOP_WORDS_ES | STOP_WORDS_EN


def tokenizar(texto: str) -> list[str]:
    """Tokeniza texto removiendo stop words y normalizando.

    - Minúsculas
    - Remueve puntuación
    - Filtra stop words
    - Filtra tokens muy cortos (<2 chars)
    """
    if not texto:
        return []

    texto = texto.lower()
    tokens = re.findall(r'[a-záéíóúñü0-9]+', texto)
    return [t for t in tokens if len(t) >= 2 and t not in STOP_WORDS]


def calcular_tf(tokens: list[str]) -> dict[str, float]:
    """Calcula Term Frequency (frecuencia normalizada)."""
    if not tokens:
        return {}

    conteo = Counter(tokens)
    max_freq = max(conteo.values())

    # TF normalizado: freq / max_freq
    return {term: freq / max_freq for term, freq in conteo.items()}


def calcular_idf(documentos: list[list[str]]) -> dict[str, float]:
    """Calcula Inverse Document Frequency.

    IDF(t) = log(N / df(t)) + 1  (suavizado)
    """
    n_docs = len(documentos)
    if n_docs == 0:
        return {}

    # Contar en cuántos documentos aparece cada término
    df: dict[str, int] = {}
    for doc in documentos:
        for term in set(doc):
            df[term] = df.get(term, 0) + 1

    # IDF con suavizado
    return {term: math.log(n_docs / count) + 1 for term, count in df.items()}


def calcular_tfidf(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """Calcula TF-IDF para un documento."""
    tf = calcular_tf(tokens)
    return {term: tf_val * idf.get(term, 1.0) for term, tf_val in tf.items()}


def similitud_coseno(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Calcula similitud coseno entre dos vectores TF-IDF."""
    if not vec_a or not vec_b:
        return 0.0

    # Términos en común
    terminos_comunes = set(vec_a.keys()) & set(vec_b.keys())

    if not terminos_comunes:
        return 0.0

    # Producto punto
    dot_product = sum(vec_a[t] * vec_b[t] for t in terminos_comunes)

    # Magnitudes
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot_product / (mag_a * mag_b)


class MotorTFIDF:
    """Motor de búsqueda TF-IDF con re-ranking de resultados FTS5.

    Arquitectura:
    - FTS5 hace el retrieval rápido (candidatos)
    - TF-IDF re-rankea por relevancia semántica
    - Se combinan ambos scores para el resultado final
    """

    def __init__(self):
        self._idf_cache: Optional[dict[str, float]] = None
        self._docs_cache: list[list[str]] = []

    def construir_idf(self, textos: list[str]):
        """Construye el índice IDF a partir de los textos de todas las entradas."""
        documentos = [tokenizar(t) for t in textos]
        self._idf_cache = calcular_idf(documentos)
        self._docs_cache = documentos

    def score_tfidf(self, query: str, texto_entrada: str) -> float:
        """Calcula el score TF-IDF de una entrada contra el query."""
        if not self._idf_cache:
            return 0.0

        tokens_query = tokenizar(query)
        tokens_doc = tokenizar(texto_entrada)

        if not tokens_query or not tokens_doc:
            return 0.0

        vec_query = calcular_tfidf(tokens_query, self._idf_cache)
        vec_doc = calcular_tfidf(tokens_doc, self._idf_cache)

        return similitud_coseno(vec_query, vec_doc)

    def rerankear(self, query: str, entradas_texto: list[tuple[str, str, float]]) -> list[tuple[str, float]]:
        """Re-rankear entradas combinando FTS5 score con TF-IDF.

        Args:
            query: Texto de búsqueda
            entradas_texto: Lista de (id, texto_completo, fts5_score)

        Returns:
            Lista de (id, score_combinado) ordenada por relevancia
        """
        if not self._idf_cache or not entradas_texto:
            return [(eid, fscore) for eid, _, fscore in entradas_texto]

        scores = []
        for eid, texto, fts5_score in entradas_texto:
            tfidf_score = self.score_tfidf(query, texto)

            # Combinar scores: 60% TF-IDF + 40% FTS5
            # TF-IDF tiene peso mayor porque entiende relevancia semántica
            score_combinado = 0.6 * tfidf_score + 0.4 * fts5_score

            scores.append((eid, score_combinado))

        # Ordenar por score descendente
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


def texto_entrada_compacto(entrada_dict: dict) -> str:
    """Extrae texto plano de una entrada para indexar con TF-IDF.

    Combina título + contenido + etiquetas en un solo string.
    """
    partes = []

    if entrada_dict.get("titulo"):
        partes.append(entrada_dict["titulo"])

    contenido = entrada_dict.get("contenido", {})
    if isinstance(contenido, dict):
        for clave, valor in contenido.items():
            partes.append(f"{clave} {valor}")
    elif isinstance(contenido, str):
        partes.append(contenido)

    if entrada_dict.get("etiquetas"):
        partes.append(" ".join(entrada_dict["etiquetas"]))

    return " ".join(partes)
