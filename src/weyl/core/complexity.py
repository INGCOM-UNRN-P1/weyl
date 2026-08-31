"""Analizador de transformaciones algorítmicas y complejidad en WEYL."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table


def _contar_anidacion_bucles(cuerpo: str) -> int:
    """Calcula el nivel máximo de anidamiento de bucles for/while en el cuerpo de una función."""
    lineas = cuerpo.splitlines()
    profundidad_actual = 0
    max_profundidad = 0
    
    for l in lineas:
        if re.search(r"\b(for|while)\b", l):
            profundidad_actual += 1
            if profundidad_actual > max_profundidad:
                max_profundidad = profundidad_actual
        if "}" in l and profundidad_actual > 0:
            profundidad_actual -= 1

    return max_profundidad


def _es_recursiva(fn_name: str, cuerpo: str) -> bool:
    """Detecta si la función se invoca a sí misma en su cuerpo."""
    pattern = rf"\b{re.escape(fn_name)}\s*\("
    return len(re.findall(pattern, cuerpo)) >= 1


def auditar_transformaciones_algoritmicas(
    archivo_estudiante: Path,
    archivo_modelo: Path,
    console: Optional[Console] = None,
) -> List[Dict[str, Any]]:
    """Compara patrones algorítmicos (bucles, recursión vs iteración)."""
    cons = console or Console()
    from weyl.core.differ import _extraer_mapa_funciones

    txt_est = Path(archivo_estudiante).read_text(encoding="utf-8", errors="replace") if Path(archivo_estudiante).is_file() else ""
    txt_mod = Path(archivo_modelo).read_text(encoding="utf-8", errors="replace") if Path(archivo_modelo).is_file() else ""

    fns_est = _extraer_mapa_funciones(txt_est)
    fns_mod = _extraer_mapa_funciones(txt_mod)

    transformaciones: List[Dict[str, Any]] = []

    comunes = sorted(set(fns_est.keys()) & set(fns_mod.keys()))
    for fn in comunes:
        c_est = fns_est[fn]
        c_mod = fns_mod[fn]

        rec_mod = _es_recursiva(fn, c_mod)
        rec_est = _es_recursiva(fn, c_est)

        if rec_mod and not rec_est:
            transformaciones.append({
                "funcion": fn,
                "tipo": "Recursión → Iteración",
                "descripcion": "El modelo utiliza recursión mientras que el estudiante implementó un bucle iterativo.",
            })
        elif not rec_mod and rec_est:
            transformaciones.append({
                "funcion": fn,
                "tipo": "Iteración → Recursión",
                "descripcion": "El modelo utiliza iteración mientras que el estudiante implementó recursión.",
            })

        nest_est = _contar_anidacion_bucles(c_est)
        nest_mod = _contar_anidacion_bucles(c_mod)

        if nest_mod >= 2 and nest_est < nest_mod:
            transformaciones.append({
                "funcion": fn,
                "tipo": "Optimización Algorítmica (Menor anidación)",
                "descripcion": f"Redujo la anidación de bucles de {nest_mod} (O(N^{nest_mod})) a {nest_est} (O(N^{nest_est})).",
            })

    tabla = Table(title=f"🧠 Transformaciones Algorítmicas Detectadas: {Path(archivo_estudiante).name}", border_style="cyan")
    tabla.add_column("Función", style="bold cyan")
    tabla.add_column("Transformación", style="green")
    tabla.add_column("Detalle", style="white")

    for t in transformaciones:
        tabla.add_row(f"{t['funcion']}()", t["tipo"], t["descripcion"])

    if not transformaciones:
        tabla.add_row("—", "Algoritmos equivalentes", "Estructuras de control y paradigmas equivalentes al modelo.")

    cons.print(tabla)
    return transformaciones
