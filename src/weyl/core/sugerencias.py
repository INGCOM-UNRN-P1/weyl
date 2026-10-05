"""Sugerencias de refactorización a partir de la solución modelo (QoL #1028), solo para el docente.

Compara cada función de la entrega con la homónima de la solución y propone qué mirar (largo,
anidamiento de lazos, condiciones, auxiliares que la solución separa) sin mostrar el código de la
solución: el texto es para que el docente arme la devolución, no para pasárselo al estudiante tal
cual. Por eso el comando exige `--docente`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from weyl.core.complexity import _contar_anidacion_bucles
from weyl.core.differ import _extraer_mapa_funciones


@dataclass
class Sugerencia:
    funcion: str
    aspecto: str
    detalle: str


def _lineas_de_codigo(cuerpo: str) -> int:
    return sum(1 for l in cuerpo.splitlines() if l.strip() and l.strip() not in ("{", "}"))


def _condiciones(cuerpo: str) -> int:
    return len(re.findall(r"\b(if|else if|case|while|for)\b|&&|\|\||\?", cuerpo))


def _llamadas(cuerpo: str, funciones: Dict[str, str]) -> set:
    return {f for f in funciones if re.search(rf"\b{re.escape(f)}\s*\(", cuerpo)}


def sugerir(estudiante: Path, modelo: Path) -> List[Sugerencia]:
    fns_e = _extraer_mapa_funciones(Path(estudiante).read_text(encoding="utf-8", errors="replace"))
    fns_m = _extraer_mapa_funciones(Path(modelo).read_text(encoding="utf-8", errors="replace"))
    sugerencias: List[Sugerencia] = []
    for fn in sorted(set(fns_e) & set(fns_m)):
        e, m = fns_e[fn], fns_m[fn]
        le, lm = _lineas_de_codigo(e), _lineas_de_codigo(m)
        if le > 2 * lm and le - lm >= 10:
            sugerencias.append(Sugerencia(fn, "largo", f"{le} líneas contra {lm} de la solución: probablemente haga de más "
                                                       "o repita código; conviene buscar qué parte se puede extraer."))
        ae, am = _contar_anidacion_bucles(e), _contar_anidacion_bucles(m)
        if ae > am:
            sugerencias.append(Sugerencia(fn, "anidamiento", f"anida {ae} lazos y la solución {am}: puede haber un recorrido "
                                                             "de más (¿se recalcula algo en cada vuelta?)."))
        ce, cm = _condiciones(e), _condiciones(m)
        if ce > cm + 3:
            sugerencias.append(Sugerencia(fn, "condiciones", f"{ce} decisiones contra {cm}: suele indicar casos especiales "
                                                             "que el caso general ya cubre."))
        auxiliares = (_llamadas(m, fns_m) - {fn}) - _llamadas(e, fns_e)
        if auxiliares:
            sugerencias.append(Sugerencia(fn, "modularidad", f"la solución delega en {len(auxiliares)} función(es) auxiliar(es) "
                                                             "que esta versión resuelve adentro: proponé separar esa parte."))
    return sugerencias
