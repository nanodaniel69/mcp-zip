# Decisiones Técnicas — mcp-zip

### decision | 2026-07-14 | resuelto
Usar formato .md como store primario
decision: Los .md son el store primario (git-friendly, human-readable)
rationale: Formato nativo para LLMs, legible por humanos, compatible con git
impact: 53% menos tokens que formato tradicional markdown

### decision | 2026-07-14 | resuelto
SQLite FTS5 como índice de búsqueda
decision: Usar SQLite FTS5 en vez de vectores o búsqueda lineal
rationale: Viene con Python (zero dependencias), búsqueda full-text rápida, BM25 ranking
impact: Búsqueda instantánea sin modelo ML

### decision | 2026-07-14 | resuelto
TF-IDF para re-ranking semántico
decision: Agregar capa TF-IDF sobre FTS5 (60% TF-IDF + 40% FTS5)
rationale: FTS5 hace retrieval rápido, TF-IDF re-rankea por relevancia semántica
impact: Mejor ranking que FTS5 solo, sin dependencias ML

### decision | 2026-07-15 | resuelto
JSON como store secundario
decision: Generar archivos .json como cache estructurado junto con .md
rationale: Parseo rápido, acceso programático, base para APIs futuras
impact: Triple store (.md + .json + SQLite) para diferentes casos de uso

### decision | 2026-07-15 | resuelto
Todo en español
decision: Nombres de herramientas, docs, mensajes — 100% español
rationale: Comunidad hispanohablante, diferenciación en el mercado
impact: Más accesible para devs hispanohablantes

### decision | 2026-07-15 | resuelto
Auto-archivado en memoria_iniciar
decision: Archivar entradas >30 días automáticamente al iniciar sesión
rationale: Mantiene archivos .md livianos sin intervención manual
impact: Archivos activos siempre <300 tokens/mes

### decision | 2026-07-15 | resuelto
Formato .mcp-zip para exportar/importar
decision: Formato comprimido ZIP con .md + .json + metadata
rationale: Backup portátil, transferencia de proyectos, migración
impact: Los proyectos son portátiles y exportables
