"""Comparador de proyectos modulares y auditoría de memoria entre revisiones en WEYL."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List
from weyl.core.differ import comparar_archivos_c


def comparar_directorios_modulares(dir_estudiante: Path, dir_modelo: Path) -> Dict[str, Any]:
    """Realiza diffing semántico cruzado entre proyectos modulares con múltiples archivos .c."""
    archivos_est = {p.name: p for p in dir_estudiante.glob("**/*.c")} if dir_estudiante.is_dir() else {}
    archivos_mod = {p.name: p for p in dir_modelo.glob("**/*.c")} if dir_modelo.is_dir() else {}

    todos_archivos = sorted(set(archivos_est.keys()) | set(archivos_mod.keys()))
    modulos = []
    similitudes = []

    for fname in todos_archivos:
        p_est = archivos_est.get(fname)
        p_mod = archivos_mod.get(fname)

        if p_est and not p_mod:
            modulos.append({
                "archivo": fname,
                "estado": "MODULO_EXTRA",
                "similitud": 0.0,
                "detalle": "Archivo C creado por el estudiante no presente en el modelo.",
            })
        elif not p_est and p_mod:
            modulos.append({
                "archivo": fname,
                "estado": "MODULO_FALTANTE",
                "similitud": 0.0,
                "detalle": "Archivo C requerido ausente en la entrega.",
            })
        else:
            rep = comparar_archivos_c(p_est, p_mod)
            sim = rep.similitud_global
            similitudes.append(sim)
            modulos.append({
                "archivo": fname,
                "estado": "COINCIDENTE" if sim >= 0.95 else "DIVERGENTE",
                "similitud": round(sim * 100.0, 1),
                "funciones_estudiante": rep.total_funciones_estudiante,
                "funciones_modelo": rep.total_funciones_modelo,
            })

    promedio = sum(similitudes) / len(similitudes) * 100.0 if similitudes else 0.0
    return {
        "directorio_estudiante": str(dir_estudiante),
        "directorio_modelo": str(dir_modelo),
        "total_archivos_estudiante": len(archivos_est),
        "total_archivos_modelo": len(archivos_mod),
        "similitud_promedio_pct": round(promedio, 1),
        "modulos": modulos,
    }


def auditar_gestion_memoria_revisiones(dir_r1: Path, dir_r2: Path) -> Dict[str, Any]:
    """Audita cambios en llamadas a malloc, calloc, realloc y free entre revisiones sucesivas."""
    def contar_operaciones(ruta: Path) -> Dict[str, int]:
        txt = ""
        if ruta.is_file():
            txt = ruta.read_text(encoding="utf-8", errors="replace")
        elif ruta.is_dir():
            for p in ruta.glob("**/*.c"):
                txt += p.read_text(encoding="utf-8", errors="replace") + "\n"

        return {
            "malloc": len(re.findall(r"\bmalloc\s*\(", txt)),
            "calloc": len(re.findall(r"\bcalloc\s*\(", txt)),
            "realloc": len(re.findall(r"\brealloc\s*\(", txt)),
            "free": len(re.findall(r"\bfree\s*\(", txt)),
        }

    m1 = contar_operaciones(dir_r1)
    m2 = contar_operaciones(dir_r2)

    total_alloc_r1 = m1["malloc"] + m1["calloc"] + m1["realloc"]
    total_alloc_r2 = m2["malloc"] + m2["calloc"] + m2["realloc"]

    balance_r1 = total_alloc_r1 - m1["free"]
    balance_r2 = total_alloc_r2 - m2["free"]

    mejora_fugas = balance_r2 < balance_r1

    return {
        "r1": {**m1, "total_reservas": total_alloc_r1, "balance_neto": balance_r1},
        "r2": {**m2, "total_reservas": total_alloc_r2, "balance_neto": balance_r2},
        "mejora_balance": mejora_fugas,
        "detalle": "Se incrementó la tasa de liberación con free() respecto a R1" if mejora_fugas else "Balance de memoria estable o sin cambios sustanciales",
    }
