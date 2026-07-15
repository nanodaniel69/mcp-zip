# mcp-zip 🗜️

**Memoria comprimida para agentes de IA.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-purple.svg)](https://modelcontextprotocol.io)

> **mcp-zip** es un servidor MCP que comprime el contexto de tu agente de IA. En vez de leer archivos completos (miles de tokens), busca solo lo relevante (decenas de tokens). Como un ZIP, pero para la memoria del agente.

## El Problema

Tu agente de IA olvida todo cada vez que termina una sesión. Para recordar, tiene que leer archivos completos de contexto — consumiendo miles de tokens en cada conversación. Al final del día, llegás al rate limit.

## La Solución

**mcp-zip** comprime la memoria del agente en archivos `.md` compactos, optimizados para consumo de LLMs. Con búsqueda FTS5, tu agente encuentra lo relevante en milisegundos sin leer archivos completos.

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

| Herramienta | Descripción |
|-------------|-------------|
| `memoria_iniciar` | Crea un proyecto nuevo con estructura de memoria |
| `memoria_escribir` | Registra una entrada (bug, decisión, implementación, plan) |
| `memoria_buscar` | Busca entradas por texto completo con ranking FTS5 |
| `memoria_leer` | Lee un archivo de memoria completo |
| `memoria_resumen` | Resumen compacto del estado del proyecto |
| `memoria_listar` | Lista todos los proyectos |
| `memoria_archivar` | Archiva entradas resueltas antiguas en bóveda |
| `memoria_importar` | Migra archivos .md existentes al sistema |
| `memoria_exportar` | Exporta un archivo de memoria |

## Ejemplo de Uso

```
Usuario: "Creá el proyecto ferreteria con stack Next.js + Prisma"

Agente llama memoria_iniciar("ferreteria", "Next.js + Prisma")
→ ✅ Proyecto 'ferreteria' inicializado en ~/.memoria/proyectos/ferreteria/

Usuario: "Anotá que el bug del color detection se resolvió"

Agente llama memoria_escribir("ferreteria", "bug", "Color detection falla",
    contexto="Pinturas Tekbond/Miura se fusionan",
    solucion="Spread de attributes en parser FGP",
    etiquetas="parser,fgp,colores")
→ ✅ Entrada 'bug-2026-07-14-color-detection-falla' registrada en errores.md

Usuario: "¿Qué errores tiene ferreteria?"

Agente llama memoria_buscar("ferreteria", "color detection")
→ 🔍 1 resultado para 'color detection' en 'ferreteria':
   1. Color detection falla (bug | 2026-07-14 | resuelto)
      ctx: Pinturas Tekbond/Miura se fusionan
      fix: Spread de attributes en parser FGP
      tags: parser,fgp,colores
```

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

Las entradas resueltas con más de 30 días se archivan automáticamente en la bóveda:

```
~/.memoria/proyectos/ferreteria/
├── errores.md          ← Entradas activas
├── decisiones.md       ← Entradas activas
├── boveda/
│   ├── errores-2026-06.md      ← Archivados de junio
│   └── decisiones-2026-06.md   ← Archivados de junio
└── memoria.db           ← Índice FTS5
```

## Migración

Si ya tenés archivos `.md` de contexto existentes:

```bash
# El agente llama:
memoria_importar("ferreteria", "/home/user/proyectos/ferreteria/context/")
→ 📥 Importación completada: 5 archivos, 23 entradas
```

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MEMORIA_ROOT` | Directorio raíz de almacenamiento | `~/.memoria` |

## Licencia

MIT — Ver [LICENSE](LICENSE)

---

**mcp-zip** — Comprime la memoria de tu agente. Ahorra tokens. Nunca olvide. 🗜️
