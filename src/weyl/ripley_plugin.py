"""Plugin de WEYL para integración con RIPLEY."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from weyl.core.differ import comparar_archivos_c


class WeylPlugin:
    """Plugin de diffing semántico y comparación estructural para Ripley."""

    name = "semantic_diff"
    version = "0.1.0"

    def is_available(self) -> bool:
        return True

    def execute(self, workspace: Path, manifest_config: Dict[str, Any]) -> Dict[str, Any]:
        modelo = manifest_config.get("solution_path")
        if not modelo or not Path(modelo).is_file():
            return {"ok": True, "observaciones": []}

        archivos = list(workspace.glob("*.c"))
        if not archivos:
            return {"ok": True, "observaciones": []}

        rep = comparar_archivos_c(archivos[0], Path(modelo))
        observaciones = []

        for d in rep.funciones:
            if d.estado == "ELIMINADA":
                observaciones.append({
                    "codigo": "MISSING_FUNCTION",
                    "severidad": "ERROR",
                    "mensaje": f"Falta implementar la función obligatoria '{d.nombre}()'.",
                })

        return {
            "ok": len(observaciones) == 0,
            "total_funciones": len(rep.funciones),
            "observaciones": observaciones,
        }
