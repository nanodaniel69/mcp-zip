# mcp-zip 🗜️

**Memoria comprimida para agentes de IA.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-purple.svg)](https://modelcontextprotocol.io)

> **mcp-zip** es un servidor MCP que comprime el contexto de tu agente de IA. En vez de leer archivos completos (miles de tokens), busca solo lo relevante (decenas de tokens). Como un ZIP, pero para la memoria del agente.

## El Problema

Tu agente de IA olvida todo cada vez que termina una sesión. Para recordar, tiene que leer archivos completos de contexto — consumiendo miles de tokens en cada conversación. Al final del día, llegás al rate limit.

## La Solución

**mcp-zip** comprime la memoria del agente en archivos `.md` compactos, optimizados para consumo de LLMs. Con búsqueda FTS5 + TF-IDF, tu agente encuentra lo relevante en milisegundos sin leer archivos completos.

## Arquitectura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  .md files   │────▶│  .json cache │────▶│  SQLite      │
│  (store)     │     │  (estructura)│     │  (índice)    │
│  git-friendly│     │  parseo rápido│    │  FTS5+TF-IDF │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  Humanos leen       APIs acceden        Agente busca
  y commitean        programátic.        instantáneo
```

### Flujo de Trabajo

```
INICIAR SESIÓN:
  memoria_iniciar("ferreteria")
  → Auto-archiva entradas >30 días
  → ✅ Proyecto activo

ESCRIBIR:
  memoria_escribir("ferreteria", "bug", "Color falla", ...)
  → Guarda en .md (git)
  → Genera .json (cache)
  → Indexa en SQLite (búsqueda)

BUSCAR:
  memoria_buscar("ferreteria", "color detection")
  → SQLite FTS5 + TF-IDF busca (~700 tokens)
  → Devuelve solo entradas relevantes

LEER:
  memoria_leer("ferreteria", "resumen")
  → Lee .md completo (~500 tokens)
  → Solo para contexto general
```

## Instalación

```bash
pip install mcp-zip
```

## Configurar en tu Editor

### Zed

Agrega en `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "zip": {
      "command": "mcp-zip"
    }
  }
}
```

### Claude Desktop

Agrega en `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zip": {
      "command": "mcp-zip"
    }
  }
}
```

### Cursor

Agrega en `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "zip": {
      "command": "mcp-zip"
    }
  }
}
```

### Cualquier Cliente MCP

```json
{
  "mcpServers": {
    "zip": {
      "command": "mcp-zip",
      "env": {
        "MEMORIA_ROOT": "~/.memoria"
      }
    }
  }
}
```

## Herramientas

| Herramienta | Descripción | Tokens |
|-------------|-------------|--------|
| `memoria_iniciar` | Crea/reactiva proyecto + auto-archiva | ~50 |
| `memoria_escribir` | Registra entrada (bug, decisión, plan) | ~100 |
| `memoria_buscar` | Búsqueda semántica FTS5 + TF-IDF | ~700 |
| `memoria_leer` | Lee archivo completo | ~500-5000 |
| `memoria_resumen` | Resumen compacto del estado | ~500 |
| `memoria_listar` | Lista todos los proyectos | ~100 |
| `memoria_archivar` | Archiva entradas >30 días en bóveda | ~50 |
| `memoria_importar` | Migra .md existentes al sistema | ~200 |
| `memoria_exportar` | Exporta archivo de memoria | variable |
| `memoria_estadisticas` | Métricas de uso y ahorro de tokens | ~300 |
| `memoria_sincronizar` | Sync JSON + SQLite de todos los proyectos | ~500 |
| `memoria_exportar_zip` | Exporta proyecto a formato .mcp-zip | ~200 |
| `memoria_importar_zip` | Importa proyecto desde .mcp-zip | ~300 |
| `memoria_listar_zip` | Lista contenido de un .mcp-zip | ~100 |

## Flujo Óptimo (Ahorra Tokens)

### ❌ Mal (consume ~50,000 tokens/sesión)

```
# Leer TODO el contexto cada vez
memoria_leer("ferreteria", "errores")      # 3,716 tokens
memoria_leer("ferreteria", "decisiones")    # 5,901 tokens
memoria_leer("ferreteria", "implementacion") # 2,862 tokens
```

### ✅ Bien (consume ~3,500 tokens/sesión)

```
# Resumen general
memoria_resumen("ferreteria")              # 500 tokens

# Búsqueda específica
memoria_buscar("ferreteria", "parser")     # 700 tokens
memoria_buscar("ferreteria", "color")      # 700 tokens

# Lectura solo si es necesario
memoria_leer("ferreteria", "resumen")      # 500 tokens
```

**Ahorro: 93% de tokens por sesión.**

## Formato Compacto

**mcp-zip** usa un formato `.md` optimizado para modelos de IA:

```markdown
### bug | 2026-07-14 | resuelto
Color detection no funciona
ctx: Pinturas Tekbond/Miura se fusionan
root: paso 8 parser FGP, result.attributes sobreescribe objeto
fix: result.attributes = { ...result.attributes, features }
tags: parser,fgp,colores
files: src/services/normalization/parsers/fgp.parser.ts
```

**vs formato tradicional (2x más tokens):**

```markdown
## [2026-07-14] Bug: Color detection no funciona 🟢 Resuelto

- **Contexto**: Pinturas Tekbond/Miura se fusionan al no detectar color
- **Causa raíz**: En el paso 8 del parser FGP, `result.attributes = { features: ... }` SOBREESCRIBÍA el objeto
- **Solución**: Cambiar por `result.attributes = { ...result.attributes, features: ... }`
- **Estado**: 🟢 Resuelto
```

## Bóveda de Archivado

Las entradas resueltas con más de 30 días se archivan automáticamente al iniciar sesión:

```
~/.memoria/proyectos/ferreteria/
├── errores.md          ← Entradas activas
├── errores.json        ← Cache estructurado
├── decisiones.md       ← Entradas activas
├── decisiones.json     ← Cache estructurado
├── memoria.db          ← Índice FTS5 + TF-IDF
└── boveda/
    ├── errores-2026-06.md      ← Archivados de junio
    ├── errores-2026-06.json    ← Cache de archivados
    ├── decisiones-2026-06.md
    └── decisiones-2026-06.json
```

## Stores de Almacenamiento

| Store | Formato | Para Qué | Quién lo Lee |
|-------|---------|----------|--------------|
| `.md` | Markdown compacto | Git, humanos, backup | Cualquiera |
| `.json` | JSON estructurado | Acceso programático | Python, APIs |
| `.db` | SQLite FTS5 + TF-IDF | Búsqueda instantánea | Motor de búsqueda |

## Migración

Si ya tenés archivos `.md` de contexto existentes:

```bash
# El agente llama:
memoria_importar("ferreteria", "/home/user/proyectos/ferreteria/context/")
→ 📥 Importación completada: 5 archivos, 23 entradas
→ 📄 JSON sincronizado automáticamente
```

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MEMORIA_ROOT` | Directorio raíz de almacenamiento | `~/.memoria` |

## Formato .mcp-zip

Formato comprimido para exportar/importar proyectos completos:

```bash
# Exportar proyecto
memoria_exportar_zip("ferreteria")
→ 📦 ferreteria.mcp-zip (24.5 KB → 8.2 KB comprimido)

# Importar proyecto
memoria_importar_zip("/backup/ferreteria.mcp-zip")
→ 📥 Proyecto 'ferreteria' importado (47 entradas)

# Listar contenido
memoria_listar_zip("ferreteria.mcp-zip")
→ 📋 Contenido:
   - errores.md (12 KB)
   - errores.json (8 KB)
   - decisiones.md (18 KB)
   - ...
```

## Estadísticas

```bash
memoria_estadisticas("ferreteria")
→ 📊 Estadísticas:
   - Entradas: 47 (23 bugs, 15 decisiones, 9 planes)
   - Activas: 31 | Archivadas: 16
   - 💰 Ahorro: 93% (46,500 tokens/sesión)
```

## Sincronización

```bash
memoria_sincronizar()
→ 🔄 Sincronizando todos los proyectos...
   - ferreteria: ✅ JSON + SQLite reconstruido
   - matucho: ✅ JSON + SQLite reconstruido
```

## Stats del Proyecto

```
Líneas de código:  ~2,200
Tests:             35/35 ✅
Dependencias:      2 (fastmcp, pyyaml)
Formato:           .md + .json + SQLite
Búsqueda:          FTS5 + TF-IDF (sin ML)
```

## Licencia

MIT — Ver [LICENSE](LICENSE)

---

**mcp-zip** — Comprime la memoria de tu agente. Ahorra tokens. Nunca olvide. 🗜️
