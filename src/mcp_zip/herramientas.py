"""Herramientas MCP para mcp-zip."""

from typing import Optional
from .formateador import Entrada, generar_id
from .almacenamiento import (
    crear_proyecto,
    proyecto_existe,
    listar_proyectos,
    leer_archivo,
    agregar_entrada,
    leer_entradas,
    mover_a_boveda,
    ARCHIVOS_ESTANDAR,
)
from .motor import MotorBusqueda
from .importador import importar_desde_contexto


def memoria_iniciar(nombre: str, stack: str = "") -> str:
    """Crea un proyecto nuevo con la estructura de memoria.

    Args:
        nombre: Nombre del proyecto (ej: "ferreteria")
        stack: Stack tecnológico opcional (ej: "Next.js + Prisma")

    Returns:
        Mensaje de confirmación con la ruta del proyecto
    """
    if proyecto_existe(nombre):
        return f"⚠️ Proyecto '{nombre}' ya existe. Usá memoria_leer o memoria_buscar."

    crear_proyecto(nombre, stack)
    return f"✅ Proyecto '{nombre}' inicializado en ~/.memoria/proyectos/{nombre}/"


def memoria_escribir(
    nombre: str,
    tipo: str,
    titulo: str,
    contexto: str = "",
    causa_raiz: str = "",
    solucion: str = "",
    decision: str = "",
    rationale: str = "",
    impacto: str = "",
    archivos: str = "",
    etiquetas: str = "",
    estado: str = "activo",
) -> str:
    """Escribe una entrada de memoria en formato compacto.

    Args:
        nombre: Nombre del proyecto
        tipo: Tipo de entrada (bug, decision, implementacion, plan)
        titulo: Título de la entrada
        contexto: Contexto del problema o decisión
        causa_raiz: Causa raíz (para bugs)
        solucion: Solución implementada
        decision: Decisión tomada (para decisiones)
        rationale: Razonamiento de la decisión
        impacto: Impacto de la entrada
        archivos: Archivos afectados (separados por coma)
        etiquetas: Etiquetas (separadas por coma)
        estado: Estado (activo, resuelto, pendiente)

    Returns:
        Mensaje de confirmación con el ID de la entrada
    """
    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe. Usá memoria_iniciar primero."

    # Mapear tipo de archivo
    tipo_archivo_map = {
        "bug": "errores",
        "decision": "decisiones",
        "implementacion": "implementacion",
        "plan": "plan",
    }
    tipo_archivo = tipo_archivo_map.get(tipo, tipo)

    # Construir contenido
    contenido = {}
    if contexto:
        contenido["ctx"] = contexto
    if causa_raiz:
        contenido["root"] = causa_raiz
    if solucion:
        contenido["fix"] = solucion
    if decision:
        contenido["decision"] = decision
    if rationale:
        contenido["rationale"] = rationale
    if impacto:
        contenido["impact"] = impacto

    # Parsear listas
    etiquetas_list = [e.strip() for e in etiquetas.split(',') if e.strip()] if etiquetas else []
    archivos_list = [a.strip() for a in archivos.split(',') if a.strip()] if archivos else []

    # Crear entrada
    entrada = Entrada(
        tipo=tipo,
        titulo=titulo,
        estado=estado,
        contenido=contenido,
        etiquetas=etiquetas_list,
        archivos_afectados=archivos_list,
        proyecto=nombre,
    )

    # Guardar en archivo
    agregar_entrada(nombre, tipo_archivo, entrada)

    # Indexar en motor de búsqueda
    motor = MotorBusqueda(nombre)
    motor.indexar_entrada(entrada)

    return f"✅ Entrada '{entrada.id}' registrada en {tipo_archivo}.md — {entrada.fecha}"


def memoria_buscar(nombre: str, query: str, solo_activos: bool = False) -> str:
    """Busca entradas de memoria por texto completo.

    Args:
        nombre: Nombre del proyecto
        query: Texto a buscar
        solo_activos: Si es True, solo busca en entradas no archivadas

    Returns:
        Resultados formateados de la búsqueda
    """
    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe."

    motor = MotorBusqueda(nombre)
    resultados = motor.buscar(query, solo_activos=solo_activos)

    if not resultados:
        return f"🔍 Sin resultados para '{query}' en '{nombre}'."

    salida = f"🔍 **{len(resultados)} resultados** para '{query}' en '{nombre}':\n\n"

    for i, r in enumerate(resultados, 1):
        fuente = f" [{r.fuente}]" if r.fuente == "boveda" else ""
        salida += f"**{i}. {r.entrada.titulo}** ({r.entrada.tipo} | {r.entrada.fecha} | {r.entrada.estado}){fuente}\n"

        for clave, valor in r.entrada.contenido.items():
            salida += f"   {clave}: {valor}\n"

        if r.entrada.etiquetas:
            salida += f"   tags: {','.join(r.entrada.etiquetas)}\n"
        salida += "\n"

    return salida


def memoria_leer(nombre: str, tipo_archivo: str = "resumen") -> str:
    """Lee un archivo de memoria completo.

    Args:
        nombre: Nombre del proyecto
        tipo_archivo: Tipo de archivo a leer (resumen, errores, decisiones, implementacion, plan)

    Returns:
        Contenido del archivo
    """
    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe."

    contenido = leer_archivo(nombre, tipo_archivo)
    if not contenido:
        return f"📄 Archivo '{tipo_archivo}.md' vacío o no existe en '{nombre}'."

    return contenido


def memoria_resumen(nombre: str) -> str:
    """Genera un resumen compacto del estado del proyecto.

    Args:
        nombre: Nombre del proyecto

    Returns:
        Resumen compacto con estadísticas
    """
    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe."

    motor = MotorBusqueda(nombre)
    stats = motor.estadisticas()

    proyectos = listar_proyectos()
    info = next((p for p in proyectos if p["nombre"] == nombre), None)

    salida = f"📋 **Resumen de {nombre}:**\n\n"
    salida += f"- Archivos: {info['archivos'] if info else '?'}\n"
    salida += f"- Líneas totales: {info['lineas'] if info else '?'}\n"
    salida += f"- Entradas indexadas: {stats['total']}\n"
    salida += f"  - Activas: {stats['activos']}\n"
    salida += f"  - Archivadas: {stats['archivados']}\n"

    if stats['por_tipo']:
        salida += f"- Por tipo: {stats['por_tipo']}\n"

    if stats['por_estado']:
        salida += f"- Por estado: {stats['por_estado']}\n"

    return salida


def memoria_listar() -> str:
    """Lista todos los proyectos con memoria.

    Returns:
        Lista de proyectos con información básica
    """
    proyectos = listar_proyectos()

    if not proyectos:
        return "📂 No hay proyectos. Usá memoria_iniciar para crear uno."

    salida = "📂 **Proyectos:**\n\n"
    for p in proyectos:
        salida += f"- **{p['nombre']}** — {p['archivos']} archivos, {p['lineas']} líneas"

        if p['tiene_boveda']:
            salida += " 📦"
        if p['tiene_db']:
            salida += " 🔍"
        salida += "\n"

    return salida


def memoria_archivar(nombre: str, dias: int = 30) -> str:
    """Archiva entradas resueltas antiguas en la bóveda.

    Args:
        nombre: Nombre del proyecto
        dias: Días de antigüedad para archivar (default: 30)

    Returns:
        Mensaje con cantidad de entradas archivadas
    """
    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe."

    archivadas = 0

    for tipo_archivo in ["errores", "decisiones"]:
        entradas = leer_entradas(nombre, tipo_archivo)
        for entrada in entradas:
            if entrada.estado == "resuelto" and not entrada.archivado:
                # Calcular antigüedad
                from datetime import datetime, timedelta
                try:
                    fecha_entrada = datetime.strptime(entrada.fecha, "%Y-%m-%d")
                    if (datetime.now() - fecha_entrada).days >= dias:
                        mover_a_boveda(nombre, tipo_archivo, entrada.id)
                        archivadas += 1
                except ValueError:
                    continue

    if archivadas > 0:
        return f"📦 {archivadas} entradas archivadas en bóveda de '{nombre}'."
    else:
        return f"📦 No hay entradas para archivar en '{nombre}' (mínimo {dias} días, estado resuelto)."


def memoria_importar(nombre: str, ruta: str) -> str:
    """Importa archivos .md desde una carpeta context/ existente.

    Args:
        nombre: Nombre del proyecto
        ruta: Ruta a la carpeta context/ (ej: /home/user/proyecto/context/)

    Returns:
        Estadísticas de importación
    """
    stats = importar_desde_contexto(nombre, ruta)

    if "error" in stats:
        return f"❌ {stats['error']}"

    salida = f"📥 Importación completada para '{nombre}':\n"
    salida += f"- Archivos importados: {stats['archivos_importados']}\n"
    salida += f"- Entradas importadas: {stats['entradas_importadas']}\n"

    if stats['errores']:
        salida += f"- Errores: {len(stats['errores'])}\n"
        for err in stats['errores'][:3]:
            salida += f"  - {err}\n"

    return salida


def memoria_exportar(nombre: str, tipo_archivo: str = "resumen") -> str:
    """Exporta un archivo de memoria (lee el contenido).

    Args:
        nombre: Nombre del proyecto
        tipo_archivo: Tipo de archivo a exportar

    Returns:
        Contenido del archivo para copiar/guardar
    """
    return memoria_leer(nombre, tipo_archivo)
