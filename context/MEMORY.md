# MCP-ZIP — Memoria Comprimida para Agentes de IA

## Stack
- Python 3.10+
- FastMCP 2.0+ (servidor MCP)
- SQLite FTS5 (búsqueda full-text)
- TF-IDF (búsqueda semántica ligera, sin ML)
- PyYAML (configuración)

## Arquitectura
```
.md (store) → .json (cache) → SQLite (índice FTS5 + TF-IDF)
```

## Estado
- Versión: 0.2.0
- PyPI: https://pypi.org/project/mcp-zip/
- GitHub: https://github.com/nanodaniel69/mcp-zip
- Tests: 46/46 ✅
- Herramientas MCP: 14

## Configuración
- Root: ~/.memoria/proyectos/
- Encoding: UTF-8
- Auto-archivado: 30 días
- Ahorro de tokens: 93%

## Decisiones Técnicas Clave
1. .md como store primario (git-friendly, legible por humanos)
2. JSON como cache estructurado (parseo rápido)
3. SQLite FTS5 como índice de búsqueda (zero dependencias)
4. TF-IDF para re-ranking semántico (60% TF-IDF + 40% FTS5)
5. Formato compacto optimizado para LLMs (~53% menos tokens)
6. Todo en español (nombres, docs, mensajes)
7. Auto-archivado al iniciar sesión (memoria_iniciar)
8. Formato .mcp-zip para exportar/importar proyectos

## Dependencias
- fastmcp>=2.0
- pyyaml>=6.0

## Archivos Principales
- src/mcp_zip/server.py — Entry point MCP
- src/mcp_zip/herramientas.py — 14 herramientas MCP
- src/mcp_zip/motor.py — Búsqueda FTS5 + TF-IDF
- src/mcp_zip/tfidf.py — Motor TF-IDF puro
- src/mcp_zip/almacenamiento.py — I/O de archivos .md
- src/mcp_zip/almacenamiento_json.py — I/O de archivos .json
- src/mcp_zip/formateador.py — Formato compacto optimizado
- src/mcp_zip/configuracion.py — Config
- src/mcp_zip/importador.py — Migración de .md existentes
