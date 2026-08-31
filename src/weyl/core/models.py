"""Modelos de datos para el diffing semántico en WEYL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DiferenciaFuncion:
    nombre: str
    estado: str                 # "MODIFICADA", "AGREGADA", "ELIMINADA", "IDENTICA"
    lineas_estudiante: int = 0
    lineas_modelo: int = 0
    similitud: float = 1.0
    cambios: List[str] = field(default_factory=list)


@dataclass
class ReporteSemanticDiff:
    archivo_estudiante: Path
    archivo_modelo: Path
    total_funciones_estudiante: int
    total_funciones_modelo: int
    funciones: List[DiferenciaFuncion] = field(default_factory=list)

    @property
    def similitud_global(self) -> float:
        if not self.funciones:
            return 1.0
        return sum(f.similitud for f in self.funciones) / len(self.funciones)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archivo_estudiante": str(self.archivo_estudiante),
            "archivo_modelo": str(self.archivo_modelo),
            "similitud_global": round(self.similitud_global, 2),
            "total_funciones_estudiante": self.total_funciones_estudiante,
            "total_funciones_modelo": self.total_funciones_modelo,
            "diferencias": [
                {
                    "nombre": f.nombre,
                    "estado": f.estado,
                    "similitud": round(f.similitud, 2),
                    "cambios": f.cambios[:5],
                }
                for f in self.funciones
            ],
        }

