# Implementación — mcp-zip

### implementacion | 2026-07-14 | resuelto
MVP inicial — 11 herramientas MCP
ctx: Crear servidor MCP con FastMCP que tenga herramientas de memoria
solucion: server.py + herramientas.py + formateador.py + motor.py + almacenamiento.py + configuracion.py
tags: mvp,fastmcp,mcp
files: src/mcp_zip/server.py,src/mcp_zip/herramientas.py,src/mcp_zip/formateador.py

### implementacion | 2026-07-14 | resuelto
Fix parser de contenido con espacios
ctx: _parsear_contenido() rompía valores multi-palabra
solucion: Almacenar contenido como JSON en SQLite, parsear con json.loads()
tags: bug,json,sqlite
files: src/mcp_zip/motor.py

### implementacion | 2026-07-14 | resuelto
Sincronización bóveda-SQLite
ctx: mover_a_boveda() no actualizaba SQLite
solucion: Agregar _actualizar_archivado_sqlite() + sync JSON
tags: boveda,sync,bug
files: src/mcp_zip/almacenamiento.py

### implementacion | 2026-07-15 | resuelto
Motor TF-IDF puro
ctx: Búsqueda semántica ligera sin modelo ML
solucion: tfidf.py con tokenizador español, stop words ES+EN, TF, IDF, similitud coseno
tags: tfidf,busqueda,semantica
files: src/mcp_zip/tfidf.py

### implementacion | 2026-07-15 | resuelto
JSON secundario como store estructurado
ctx: Cache estructurado para acceso programático rápido
solucion: almacenamiento_json.py + sync automático con .md
tags: json,store,cache
files: src/mcp_zip/almacenamiento_json.py

### implementacion | 2026-07-15 | resuelto
Auto-archivado en cada sesión
ctx: memoria_iniciar() debe archivar entradas >30 días automáticamente
solucion: _auto_archivar() se ejecuta al reactivar proyecto
tags: auto,boveda,sync
files: src/mcp_zip/herramientas.py

### implementacion | 2026-07-15 | resuelto
Fase 3: Estadísticas + sincronización + .mcp-zip
ctx: 3 nuevas herramientas para métricas, sync y formato comprimido
solucion: memoria_estadisticas() + memoria_sincronizar() + memoria_exportar_zip() + memoria_importar_zip() + memoria_listar_zip()
tags: estadisticas,sync,zip,fase3
files: src/mcp_zip/herramientas.py

### implementacion | 2026-07-15 | resuelto
Publicación en PyPI
ctx: Publicar mcp-zip como paquete pip
solucion: pyproject.toml configurado + twine upload
tags: pypi,publicacion,fase4
