"""Detector de funciones auxiliares huérfanas o no invocadas en entregas de estudiantes."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional
from rich.console import Console
from rich.table import Table


def huerfanas_via_giger(archivo: Path) -> Optional[List[str]]:
    """Pide el grafo de llamadas a `giger` (dueño de R-A6) por CLI-JSON.

    Devuelve None si giger no está instalado o su salida no es utilizable, y
    el llamador cae al detector propio.
    """
    binario = shutil.which("giger")
    if not binario:
        return None
    try:
        proc = subprocess.run([binario, "check", str(archivo), "--json"],
                              capture_output=True, text=True, timeout=30)
        datos = json.loads(proc.stdout)
        huerfanas = datos["funciones_huerfanas"]
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
        return None
    return [str(f) for f in huerfanas] if isinstance(huerfanas, list) else None


def detectar_funciones_huerfanas(
    archivo_estudiante: Path,
    archivo_modelo: Optional[Path] = None,
    console: Optional[Console] = None,
    usar_giger: bool = True,
) -> List[str]:
    """Detecta funciones en el archivo del estudiante que no son invocadas por ninguna otra función.

    Delega en `giger check --json` cuando está instalado (una sola definición
    de "huérfana" en el ecosistema); si no, usa el detector propio de abajo.
    """
    cons = console or Console()
    via_giger = huerfanas_via_giger(Path(archivo_estudiante)) if usar_giger else None
    from weyl.core.differ import _extraer_mapa_funciones

    txt_est = Path(archivo_estudiante).read_text(encoding="utf-8", errors="replace") if Path(archivo_estudiante).is_file() else ""
    fns_est = _extraer_mapa_funciones(txt_est)

    invocaciones: Dict[str, Set[str]] = {fn: set() for fn in fns_est}

    for fn_origen, cuerpo in fns_est.items():
        for fn_destino in fns_est:
            if fn_origen != fn_destino:
                pattern = rf"\b{re.escape(fn_destino)}\s*\("
                if re.search(pattern, cuerpo):
                    invocaciones[fn_origen].add(fn_destino)

    todas_invocadas: Set[str] = set()
    for llamads in invocaciones.values():
        todas_invocadas.update(llamads)

    # Funciones no invocadas excluyendo main y las que pertenezcan a la API modelo si se provee
    huerfanas = []
    for fn in fns_est:
        if fn != "main" and fn not in todas_invocadas:
            huerfanas.append(fn)
    if via_giger is not None:
        huerfanas = via_giger

    tabla = Table(title=f"🗑️ Auditoría de Funciones Huérfanas / Dead Code: {Path(archivo_estudiante).name}", border_style="yellow" if huerfanas else "green")
    tabla.add_column("Función", style="bold cyan")
    tabla.add_column("Estado", style="red" if huerfanas else "green")
    tabla.add_column("Diagnóstico", style="white")

    for h in huerfanas:
        tabla.add_row(f"{h}()", "HUÉRFANA", "Función auxiliar declarada pero jamás invocada en el archivo.")

    if not huerfanas:
        tabla.add_row("✓ Todas las funciones", "LIMPIO", "Todas las funciones auxiliares cuentan con referencias activas.")

    cons.print(tabla)
    return huerfanas
