"""Motor de extracción y diffing semántico de funciones en WEYL."""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Dict, List, Tuple

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


def comparar_archivos_c(archivo_estudiante: Path, archivo_modelo: Path) -> ReporteSemanticDiff:
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
            matcher = difflib.SequenceMatcher(None, cuerpo_e, cuerpo_m)
            ratio = matcher.ratio()
            estado = "IDENTICA" if ratio >= 0.99 else "MODIFICADA"

            diff_lines = list(difflib.unified_diff(
                cuerpo_m.splitlines(keepends=True),
                cuerpo_e.splitlines(keepends=True),
                fromfile="modelo",
                tofile="estudiante",
            ))

            diferencias.append(DiferenciaFuncion(
                nombre=fn,
                estado=estado,
                lineas_estudiante=len(cuerpo_e.splitlines()),
                lineas_modelo=len(cuerpo_m.splitlines()),
                similitud=ratio,
                cambios=[l.strip() for l in diff_lines if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))],
            ))

    return ReporteSemanticDiff(
        archivo_estudiante=archivo_estudiante,
        archivo_modelo=archivo_modelo,
        total_funciones_estudiante=len(fns_est),
        total_funciones_modelo=len(fns_mod),
        funciones=diferencias,
    )
