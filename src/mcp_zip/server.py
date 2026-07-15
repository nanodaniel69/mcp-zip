"""Servidor MCP de mcp-zip.

Memoria comprimida para agentes de IA.
Ahorra tokens, evita alucinaciones, nunca olvida.
"""

from fastmcp import FastMCP

from .herramientas import (
    memoria_iniciar,
    memoria_escribir,
    memoria_buscar,
    memoria_leer,
    memoria_resumen,
    memoria_listar,
    memoria_archivar,
    memoria_importar,
    memoria_exportar,
    memoria_estadisticas,
    memoria_sincronizar,
    memoria_exportar_zip,
    memoria_importar_zip,
    memoria_listar_zip,
)

# Crear servidor MCP
mcp = FastMCP(
    "mcp-zip",
    instructions="Memoria comprimida para agentes de IA. Ahorra tokens, evita alucinaciones.",
)

# Registrar herramientas
mcp.tool()(memoria_iniciar)
mcp.tool()(memoria_escribir)
mcp.tool()(memoria_buscar)
mcp.tool()(memoria_leer)
mcp.tool()(memoria_resumen)
mcp.tool()(memoria_listar)
mcp.tool()(memoria_archivar)
mcp.tool()(memoria_importar)
mcp.tool()(memoria_exportar)
mcp.tool()(memoria_estadisticas)
mcp.tool()(memoria_sincronizar)
mcp.tool()(memoria_exportar_zip)
mcp.tool()(memoria_importar_zip)
mcp.tool()(memoria_listar_zip)


def main():
    """Punto de entrada principal."""
    mcp.run()


if __name__ == "__main__":
    main()
