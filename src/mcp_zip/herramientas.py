"""Herramientas MCP para mcp-zip."""

import json
from pathlib import Path
from typing import Optional
from .configuracion import config
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
    """Crea o reactiva un proyecto con auto-archivado.

    Al iniciar sesión, archiva automáticamente entradas resueltas
    con más de 30 días para mantener los archivos .md livianos.

    Args:
        nombre: Nombre del proyecto (ej: "ferreteria")
        stack: Stack tecnológico opcional (ej: "Next.js + Prisma")

    Returns:
        Mensaje de confirmación con estado del proyecto
    """
    if proyecto_existe(nombre):
        # Auto-archivar entradas viejas al iniciar sesión
        archivadas = _auto_archivar(nombre)
        msg_archivado = f" 📦 {archivadas} entradas archivadas." if archivadas > 0 else ""
        return f"✅ Proyecto '{nombre}' activo.{msg_archivado} Usá memoria_buscar o memoria_escribir."

    crear_proyecto(nombre, stack)
    return f"✅ Proyecto '{nombre}' inicializado en ~/.memoria/proyectos/{nombre}/"


def _auto_archivar(nombre: str, dias: int = 30) -> int:
    """Archiva automáticamente entradas resueltas antiguas.

    Returns:
        Cantidad de entradas archivadas
    """
    from datetime import datetime, timedelta
    from .almacenamiento import leer_entradas, mover_a_boveda

    archivadas = 0
    for tipo_archivo in ["errores", "decisiones"]:
        entradas = leer_entradas(nombre, tipo_archivo)
        for entrada in entradas:
            if entrada.estado == "resuelto" and not entrada.archivado:
                try:
                    fecha_entrada = datetime.strptime(entrada.fecha, "%Y-%m-%d")
                    if (datetime.now() - fecha_entrada).days >= dias:
                        mover_a_boveda(nombre, tipo_archivo, entrada.id)
                        archivadas += 1
                except ValueError:
                    continue
    return archivadas


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


def memoria_estadisticas(nombre: str) -> str:
    """Métricas de uso y ahorro de tokens.

    Args:
        nombre: Nombre del proyecto

    Returns:
        Estadísticas detalladas del proyecto
    """
    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe."

    import os
    from datetime import datetime
    from .almacenamiento import ARCHIVOS_ESTANDAR
    from .almacenamiento_json import estadisticas_json

    # 1. Contar entradas desde SQLite
    motor = MotorBusqueda(nombre)
    stats_db = motor.estadisticas()

    # 2. Calcular tamaño de archivos
    proyecto_dir = config.proyecto_dir(nombre)
    tamanho_md = 0
    tamanho_json = 0
    archivos_md = 0
    archivos_json = 0

    for tipo in ARCHIVOS_ESTANDAR:
        md_path = proyecto_dir / ARCHIVOS_ESTANDAR[tipo]
        json_path = proyecto_dir / ARCHIVOS_ESTANDAR[tipo].replace(".md", ".json")

        if md_path.exists():
            tamanho_md += md_path.stat().st_size
            archivos_md += 1
        if json_path.exists():
            tamanho_json += json_path.stat().st_size
            archivos_json += 1

    # SQLite size
    db_path = config.db_path(nombre)
    tamanho_db = db_path.stat().st_size if db_path.exists() else 0

    tamanho_total = tamanho_md + tamanho_json + tamanho_db

    # 3. Estimar tokens (aprox 4 tokens por palabra, ~5 chars por palabra)
    tokens_md = tamanho_md // 5 * 4  # tokens en .md
    tokens_json = tamanho_json // 5 * 4  # tokens en .json

    # 4. Estimar ahorro
    # Sin mcp-zip: leer todos los .md = tokens_md
    # Con mcp-zip: buscar (~700) + resumen (~500) = ~1,200 por sesión
    ahorro_por_sesion = tokens_md - 1200 if tokens_md > 1200 else 0
    porcentaje_ahorro = (ahorro_por_sesion / tokens_md * 100) if tokens_md > 0 else 0

    # 5. Construir salida
    salida = f"📊 **Estadísticas de '{nombre}':**\n\n"
    salida += f"**Entradas:**\n"
    salida += f"- Total: {stats_db['total']}"
    if stats_db['por_tipo']:
        tipos = ", ".join(f"{k}: {v}" for k, v in stats_db['por_tipo'].items())
        salida += f" ({tipos})"
    salida += f"\n"
    salida += f"- Activas: {stats_db['activos']} | Archivadas: {stats_db['archivados']}\n\n"

    salida += f"**Archivos:**\n"
    salida += f"- .md: {archivos_md} archivos ({tamanho_md // 1024} KB)\n"
    salida += f"- .json: {archivos_json} archivos ({tamanho_json // 1024} KB)\n"
    salida += f"- .db: 1 archivo ({tamanho_db // 1024} KB)\n"
    salida += f"- Total: {tamanho_total // 1024} KB\n\n"

    salida += f"**Tokens estimados:**\n"
    salida += f"- En .md: ~{tokens_md:,} tokens\n"
    salida += f"- En .json: ~{tokens_json:,} tokens\n\n"

    salida += f"**💰 Ahorro estimado:**\n"
    if ahorro_por_sesion > 0:
        salida += f"- Sin mcp-zip: ~{tokens_md:,} tokens/sesión\n"
        salida += f"- Con mcp-zip:  ~1,200 tokens/sesión\n"
        salida += f"- Ahorro:       {porcentaje_ahorro:.0f}% ({ahorro_por_sesion:,} tokens/sesión)\n"
    else:
        salida += f"- Proyecto pequeño, ahorro mínimo\n"

    return salida


def memoria_sincronizar() -> str:
    """Sincroniza todos los proyectos (JSON + SQLite)."""
    from .almacenamiento import ARCHIVOS_ESTANDAR
    from .almacenamiento_json import sincronizar_todos

    proyectos = listar_proyectos()
    if not proyectos:
        return "📂 No hay proyectos para sincronizar."

    salida = "🔄 **Sincronizando todos los proyectos...**\n\n"

    total_entradas = 0
    for p in proyectos:
        nombre = p["nombre"]
        salida += f"**{nombre}:**\n"

        # Sincronizar JSON desde .md
        try:
            sincronizar_todos(nombre)
            salida += f"  ✅ JSON sincronizado ({p['archivos']} archivos)\n"
        except Exception as e:
            salida += f"  ❌ Error sincronizando JSON: {e}\n"

        # Reconstruir SQLite
        try:
            motor = MotorBusqueda(nombre)
            # Re-indexar todas las entradas
            for tipo in ARCHIVOS_ESTANDAR:
                entradas = leer_entradas(nombre, tipo)
                for entrada in entradas:
                    motor.indexar_entrada(entrada)
            total_entradas += motor.estadisticas()["total"]
            salida += f"  ✅ SQLite reconstruido ({motor.estadisticas()['total']} entradas)\n"
        except Exception as e:
            salida += f"  ❌ Error reconstruyendo SQLite: {e}\n"

        salida += "\n"

    salida += f"**📊 Global:**\n"
    salida += f"- Proyectos: {len(proyectos)}\n"
    salida += f"- Entradas totales: {total_entradas}\n"

    return salida


def memoria_exportar_zip(nombre: str) -> str:
    """Exporta un proyecto completo a formato .mcp-zip.

    Args:
        nombre: Nombre del proyecto

    Returns:
        Ruta del archivo .mcp-zip generado
    """
    import zipfile
    from datetime import datetime

    if not proyecto_existe(nombre):
        return f"❌ Proyecto '{nombre}' no existe."

    proyecto_dir = config.proyecto_dir(nombre)
    zip_path = proyecto_dir.parent / f"{nombre}.mcp-zip"

    metadata = {
        "nombre": nombre,
        "version": "0.1.0",
        "fecha_exportacion": datetime.now().isoformat(),
        "archivos": [],
    }

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Agregar archivos .md y .json
        for archivo in sorted(proyecto_dir.rglob("*")):
            if archivo.is_file() and archivo.suffix in (".md", ".json"):
                rel_path = str(archivo.relative_to(proyecto_dir))
                zf.write(archivo, rel_path)
                metadata["archivos"].append(rel_path)

        # Agregar metadata
        zf.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))

    tamanho_kb = zip_path.stat().st_size // 1024
    return f"📦 {nombre}.mcp-zip exportado ({tamanho_kb} KB, {len(metadata['archivos'])} archivos)"


def memoria_importar_zip(ruta_zip: str) -> str:
    """Importa un proyecto desde formato .mcp-zip.

    Args:
        ruta_zip: Ruta al archivo .mcp-zip

    Returns:
        Mensaje de confirmación
    """
    import zipfile

    ruta = Path(ruta_zip)
    if not ruta.exists():
        return f"❌ Archivo no encontrado: {ruta_zip}"

    if not ruta_zip.endswith(".mcp-zip"):
        return f"❌ No es un archivo .mcp-zip: {ruta_zip}"

    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zf:
            # Leer metadata
            if "metadata.json" not in zf.namelist():
                return "❌ Archivo .mcp-zip inválido (sin metadata.json)"

            metadata = json.loads(zf.read("metadata.json"))
            nombre = metadata["nombre"]

            # Crear proyecto
            crear_proyecto(nombre)

            # Extraer archivos
            zf.extractall(config.proyecto_dir(nombre))

            # Reconstruir SQLite
            motor = MotorBusqueda(nombre)
            for tipo in ["errores", "decisiones", "implementacion", "plan"]:
                entradas = leer_entradas(nombre, tipo)
                for entrada in entradas:
                    motor.indexar_entrada(entrada)

            total = motor.estadisticas()["total"]
            return f"📥 Proyecto '{nombre}' importado ({len(metadata['archivos'])} archivos, {total} entradas)"

    except Exception as e:
        return f"❌ Error importando: {e}"


def memoria_listar_zip(ruta_zip: str) -> str:
    """Lista el contenido de un archivo .mcp-zip.

    Args:
        ruta_zip: Ruta al archivo .mcp-zip

    Returns:
        Contenido del archivo .mcp-zip
    """
    import zipfile

    ruta = Path(ruta_zip)
    if not ruta.exists():
        return f"❌ Archivo no encontrado: {ruta_zip}"

    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zf:
            # Leer metadata
            metadata = {}
            if "metadata.json" in zf.namelist():
                metadata = json.loads(zf.read("metadata.json"))

            nombre = metadata.get("nombre", "desconocido")
            fecha = metadata.get("fecha_exportacion", "?")

            salida = f"📋 **Contenido de {Path(ruta_zip).name}:**\n\n"
            salida += f"- Proyecto: {nombre}\n"
            salida += f"- Exportado: {fecha}\n\n"

            # Listar archivos por tamaño
            archivos = []
            for info in zf.infolist():
                if info.filename != "metadata.json":
                    archivos.append((info.filename, info.file_size))

            archivos.sort(key=lambda x: x[0])
            for archivo, tamanho in archivos:
                tamanho_kb = tamanho // 1024
                salida += f"  {archivo} ({tamanho_kb} KB)\n"

            return salida

    except Exception as e:
        return f"❌ Error leyendo: {e}"
