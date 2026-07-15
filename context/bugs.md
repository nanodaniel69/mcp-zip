# Bugs — mcp-zip

### bug | 2026-07-14 | resuelto
Contenido con espacios destruido en búsqueda
ctx: _parsear_contenido() dividía por espacios, perdiendo valores multi-palabra
root: método usaba .split(' ') + .split(':') que truncaba "ctx: Pinturas Tekbond" a solo "Pinturas"
fix: Almacenar contenido como JSON en SQLite, parsear con json.loads() + fallback legacy
tags: motor,busqueda,json,sqlite
files: src/mcp_zip/motor.py

### bug | 2026-07-14 | resuelto
Bóveda desincronizada de SQLite
ctx: mover_a_boveda() solo actualizaba archivos .md, no SQLite
root: campo archivado quedaba en 0 en SQLite, entonces solo_activos devolvía entradas archivadas
fix: Agregar función _actualizar_archivado_sqlite() que sincroniza SQLite al archivar
tags: boveda,sync,sqlite
files: src/mcp_zip/almacenamiento.py

### bug | 2026-07-15 | resuelto
FastMCP parámetro description no existe
ctx: FastMCP v3.4.4 usa 'instructions', no 'description'
fix: Cambiar keyword arg de description a instructions
tags: fastmcp,config
files: src/mcp_zip/server.py
