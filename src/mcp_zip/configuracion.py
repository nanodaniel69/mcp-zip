"""Configuración de mcp-zip."""

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuración del servidor mcp-zip."""

    # Directorio raíz de almacenamiento
    root: Path = field(default_factory=lambda: Path(
        os.environ.get("MEMORIA_ROOT", os.path.expanduser("~/.memoria"))
    ))

    # Días antes de archivar una entrada resuelta
    dias_archivado: int = 30

    # Formato de fecha
    formato_fecha: str = "%Y-%m-%d"

    # Formato de timestamp
    formato_timestamp: str = "%Y-%m-%d %H:%M"

    # Codificación de archivos
    encoding: str = "utf-8"

    @property
    def proyectos_dir(self) -> Path:
        """Directorio donde se almacenan los proyectos."""
        return self.root / "proyectos"

    def proyecto_dir(self, nombre: str) -> Path:
        """Directorio de un proyecto específico."""
        return self.proyectos_dir / nombre

    def boveda_dir(self, nombre: str) -> Path:
        """Directorio de bóveda de un proyecto."""
        return self.proyecto_dir(nombre) / "boveda"

    def db_path(self, nombre: str) -> Path:
        """Ruta al archivo SQLite de un proyecto."""
        return self.proyecto_dir(nombre) / "memoria.db"


# Instancia global de configuración
config = Config()
