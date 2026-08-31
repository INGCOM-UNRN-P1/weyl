"""Generador de reportes interactivos HTML para comparación semántica en WEYL."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Optional
from weyl.core.models import ReporteSemanticDiff


def generar_html_diff(reporte: ReporteSemanticDiff, output_html: Path) -> Path:
    """Genera un reporte HTML con visualización interactiva de funciones y diffs."""
    out = Path(output_html).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for f in reporte.funciones:
        color = "#28a745" if f.estado == "IDENTICA" else "#ffc107" if f.estado == "MODIFICADA" else "#dc3545" if f.estado == "ELIMINADA" else "#17a2b8"
        cambio_txt = html.escape(f.cambios[0]) if f.cambios else "Sin cambios"
        rows.append(f"""
        <tr>
            <td><strong><code>{html.escape(f.nombre)}()</code></strong></td>
            <td><span class="badge" style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px;">{f.estado}</span></td>
            <td>{f.similitud * 100:.1f}%</td>
            <td>{f.lineas_estudiante} / {f.lineas_modelo}</td>
            <td>{cambio_txt}</td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Semántico WEYL - {html.escape(reporte.archivo_estudiante.name)}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 30px; background: #f8f9fa; }}
        .card {{ background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #212529; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .meta {{ background: #e9ecef; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border: 1px solid #dee2e6; text-align: left; }}
        th {{ background: #007bff; color: white; }}
        tr:nth-child(even) {{ background: #fdfdfd; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>⚖️ Reporte de Comparación Semántica (WEYL)</h1>
        <div class="meta">
            <p><strong>Archivo Estudiante:</strong> {html.escape(reporte.archivo_estudiante.name)}</p>
            <p><strong>Archivo Modelo:</strong> {html.escape(reporte.archivo_modelo.name)}</p>
            <p><strong>Similitud Global:</strong> <span style="font-size: 1.2em; font-weight: bold; color: #007bff;">{reporte.similitud_global * 100:.1f}%</span></p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Función</th>
                    <th>Estado</th>
                    <th>Similitud</th>
                    <th>Líneas (Est / Mod)</th>
                    <th>Detalle de Diferencias</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    out.write_text(html_content, encoding="utf-8")
    return out
