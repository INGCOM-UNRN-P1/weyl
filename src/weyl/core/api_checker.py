"""Comparador de firmas y contratos de API entre entregas y soluciones modelo en WEYL."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table


def _extraer_firmas_c(codigo: str) -> Dict[str, Dict[str, Any]]:
    """Extrae las firmas de funciones: retorno, nombre, parámetros."""
    # Eliminar comentarios
    codigo_limpio = re.sub(r'//.*?$|/\*.*?\*/', '', codigo, flags=re.DOTALL | re.MULTILINE)
    
    # Regex para capturar: tipo_retorno nombre(params) {
    re_fn = re.compile(r"^\s*((?:[a-zA-Z0-9_*]+\s+)+)([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*\{", re.MULTILINE)
    firmas = {}

    for m in re_fn.finditer(codigo_limpio):
        ret_type = m.group(1).strip()
        fn_name = m.group(2).strip()
        params_str = m.group(3).strip()

        if fn_name in ("if", "for", "while", "switch"):
            continue

        params = [p.strip() for p in params_str.split(",") if p.strip()] if params_str and params_str != "void" else []
        firmas[fn_name] = {
            "retorno": ret_type,
            "params": params,
            "cant_params": len(params),
            "firma_str": f"{ret_type} {fn_name}({params_str})",
        }

    return firmas


def comparar_firmas_api(
    archivo_estudiante: Path,
    archivo_modelo: Path,
    console: Optional[Console] = None,
) -> List[Dict[str, Any]]:
    """Compara las firmas de funciones entre la entrega del estudiante y el modelo."""
    cons = console or Console()
    txt_est = Path(archivo_estudiante).read_text(encoding="utf-8", errors="replace") if Path(archivo_estudiante).is_file() else ""
    txt_mod = Path(archivo_modelo).read_text(encoding="utf-8", errors="replace") if Path(archivo_modelo).is_file() else ""

    firmas_est = _extraer_firmas_c(txt_est)
    firmas_mod = _extraer_firmas_c(txt_mod)

    discrepancias: List[Dict[str, Any]] = []

    for fn_name, f_mod in firmas_mod.items():
        if fn_name not in firmas_est:
            discrepancias.append({
                "funcion": fn_name,
                "problema": "Función obligatoria NO implementada",
                "esperado": f_mod["firma_str"],
                "obtenido": "—",
                "severidad": "CRÍTICA",
            })
        else:
            f_est = firmas_est[fn_name]
            # Comparar cantidad de parámetros
            if f_est["cant_params"] != f_mod["cant_params"]:
                discrepancias.append({
                    "funcion": fn_name,
                    "problema": f"Cantidad incorrecta de parámetros ({f_est['cant_params']} vs esperado {f_mod['cant_params']})",
                    "esperado": f_mod["firma_str"],
                    "obtenido": f_est["firma_str"],
                    "severidad": "ALTA",
                })
            # Comparar tipo de retorno
            elif f_est["retorno"] != f_mod["retorno"]:
                discrepancias.append({
                    "funcion": fn_name,
                    "problema": f"Tipo de retorno incompatible ('{f_est['retorno']}' vs '{f_mod['retorno']}')",
                    "esperado": f_mod["firma_str"],
                    "obtenido": f_est["firma_str"],
                    "severidad": "MEDIA",
                })

    tabla = Table(title=f"📜 Verificación de API y Contratos: {Path(archivo_estudiante).name}", border_style="red" if discrepancias else "green")
    tabla.add_column("Función", style="bold cyan")
    tabla.add_column("Observación de API", style="yellow")
    tabla.add_column("Firma Requerida (Modelo)", style="green")
    tabla.add_column("Firma Entregada", style="white")

    for d in discrepancias:
        tabla.add_row(d["funcion"], d["problema"], d["esperado"], d["obtenido"])

    if not discrepancias:
        tabla.add_row("✓ Todas las funciones", "Todas las firmas respetan fielmente el contrato de API.", "OK", "OK")

    cons.print(tabla)
    return discrepancias
