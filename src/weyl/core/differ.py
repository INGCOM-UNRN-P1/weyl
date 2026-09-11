"""Motor de extracción y diffing semántico de funciones en WEYL."""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Dict, List, Tuple

from weyl.core.alpha_equiv import (
    detectar_equivalencia_for_while,
    detectar_inversion_if_else,
    normalizar_alpha_equivalencia,
)
from weyl.core.models import DiferenciaFuncion, ReporteSemanticDiff


def _eliminar_comentarios(texto: str) -> str:
    pattern = re.compile(r'//.*?$|/\*.*?\*/', re.DOTALL | re.MULTILINE)
    return re.sub(pattern, "", texto)


def _extraer_mapa_funciones(contenido: str) -> Dict[str, str]:
    """Extrae un diccionario de {nombre_funcion: cuerpo_normalizado}."""
    codigo_limpio = _eliminar_comentarios(contenido)
    re_fn = re.compile(r"^\s*(?:[a-zA-Z0-9_*]+\s+)+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{", re.MULTILINE)
    funciones = {}

    for m in re_fn.finditer(codigo_limpio):
        fn_name = m.group(1)
        if fn_name in ("if", "for", "while", "switch"):
            continue

        start_pos = m.end() - 1
        brace_count = 0
        end_pos = start_pos

        for i in range(start_pos, len(codigo_limpio)):
            if codigo_limpio[i] == '{':
                brace_count += 1
            elif codigo_limpio[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i
                    break

        cuerpo = codigo_limpio[start_pos:end_pos + 1]
        # Normalizar espacios
        cuerpo_norm = "\n".join(l.strip() for l in cuerpo.splitlines() if l.strip())
        funciones[fn_name] = cuerpo_norm

    return funciones


def comparar_archivos_c(
    archivo_estudiante: Path,
    archivo_modelo: Path,
    normalizar_alpha: bool = False,
) -> ReporteSemanticDiff:
    """Realiza una comparación semántica función por función entre dos archivos C."""
    txt_est = archivo_estudiante.read_text(encoding="utf-8", errors="ignore") if archivo_estudiante.is_file() else ""
    txt_mod = archivo_modelo.read_text(encoding="utf-8", errors="ignore") if archivo_modelo.is_file() else ""

    fns_est = _extraer_mapa_funciones(txt_est)
    fns_mod = _extraer_mapa_funciones(txt_mod)

    todos_nombres = sorted(set(fns_est.keys()) | set(fns_mod.keys()))
    diferencias: List[DiferenciaFuncion] = []

    for fn in todos_nombres:
        cuerpo_e = fns_est.get(fn)
        cuerpo_m = fns_mod.get(fn)

        if cuerpo_e and not cuerpo_m:
            diferencias.append(DiferenciaFuncion(
                nombre=fn,
                estado="AGREGADA",
                lineas_estudiante=len(cuerpo_e.splitlines()),
                similitud=0.0,
                cambios=["Función auxiliar creada por el estudiante."],
            ))
        elif not cuerpo_e and cuerpo_m:
            diferencias.append(DiferenciaFuncion(
                nombre=fn,
                estado="ELIMINADA",
                lineas_modelo=len(cuerpo_m.splitlines()),
                similitud=0.0,
                cambios=["Función requerida ausente en el código del estudiante."],
            ))
        else:
            c_e_cmp = normalizar_alpha_equivalencia(cuerpo_e) if normalizar_alpha else cuerpo_e
            c_m_cmp = normalizar_alpha_equivalencia(cuerpo_m) if normalizar_alpha else cuerpo_m

            matcher = difflib.SequenceMatcher(None, c_e_cmp, c_m_cmp)
            ratio = matcher.ratio()

            cambios_extra = []
            if normalizar_alpha_equivalencia(cuerpo_e) == normalizar_alpha_equivalencia(cuerpo_m):
                ratio = 1.0
                estado = "IDENTICA"
                cambios_extra.append("Equivalencia semántica pura (Alpha-Equivalence) comprobada.")
            elif ratio >= 0.99:
                estado = "IDENTICA"
            else:
                estado = "MODIFICADA"

            if detectar_inversion_if_else(cuerpo_e, cuerpo_m):
                cambios_extra.append("Lógica equivalente detectada con inversión de ramas if-else.")
                ratio = max(ratio, 0.90)

            if detectar_equivalencia_for_while(cuerpo_e, cuerpo_m):
                cambios_extra.append("Transformación de bucle for/while semánticamente equivalente.")
                ratio = max(ratio, 0.90)

            diff_lines = list(difflib.unified_diff(
                cuerpo_m.splitlines(keepends=True),
                cuerpo_e.splitlines(keepends=True),
                fromfile="modelo",
                tofile="estudiante",
            ))

            cambios = cambios_extra + [l.strip() for l in diff_lines if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]

            diferencias.append(DiferenciaFuncion(
                nombre=fn,
                estado=estado,
                lineas_estudiante=len(cuerpo_e.splitlines()),
                lineas_modelo=len(cuerpo_m.splitlines()),
                similitud=ratio,
                cambios=cambios,
            ))

    return ReporteSemanticDiff(
        archivo_estudiante=archivo_estudiante,
        archivo_modelo=archivo_modelo,
        total_funciones_estudiante=len(fns_est),
        total_funciones_modelo=len(fns_mod),
        funciones=diferencias,
    )
