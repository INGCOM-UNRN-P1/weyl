"""Matriz cruzada de similitud de funciones y detección de plagio semántico en WEYL."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.table import Table

from weyl.core.alpha_equiv import normalizar_alpha_equivalencia
from weyl.core.differ import _extraer_mapa_funciones


def calcular_matriz_similitud(
    archivo_a: Path,
    archivo_b: Path,
) -> Dict[str, Dict[str, float]]:
    """Calcula la matriz N x M de similitud semántica entre todas las funciones de A y B."""
    txt_a = archivo_a.read_text(encoding="utf-8", errors="replace") if archivo_a.is_file() else ""
    txt_b = archivo_b.read_text(encoding="utf-8", errors="replace") if archivo_b.is_file() else ""

    fns_a = _extraer_mapa_funciones(txt_a)
    fns_b = _extraer_mapa_funciones(txt_b)

    matriz: Dict[str, Dict[str, float]] = {}

    for name_a, code_a in fns_a.items():
        norm_a = normalizar_alpha_equivalencia(code_a)
        matriz[name_a] = {}
        for name_b, code_b in fns_b.items():
            norm_b = normalizar_alpha_equivalencia(code_b)
            ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
            matriz[name_a][name_b] = round(ratio * 100.0, 1)

    return matriz


def renderizar_matriz_rich(matriz: Dict[str, Dict[str, float]], console: Optional[Console] = None) -> None:
    """Renderiza en terminal la matriz cruzada de similitud."""
    cons = console or Console()
    if not matriz:
        cons.print("[yellow]Matriz vacía: no se encontraron funciones para comparar.[/yellow]")
        return

    cols = sorted(list(next(iter(matriz.values())).keys())) if matriz else []
    tabla = Table(title="📊 Matriz Cruzada de Similitud Semántica (Alpha-Normalized)")
    tabla.add_column("Función (A)", style="bold cyan")

    for c in cols:
        tabla.add_column(f"{c}()", justify="right")

    for fn_a, fila in sorted(matriz.items()):
        vals = []
        for c in cols:
            val = fila.get(c, 0.0)
            color = "bold green" if val >= 95 else "yellow" if val >= 70 else "dim"
            vals.append(f"[{color}]{val:.0f}%[/{color}]")
        tabla.add_row(f"{fn_a}()", *vals)

    cons.print(tabla)
