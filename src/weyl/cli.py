"""CLI de WEYL — Diffing semántico y comparación estructural en C."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from weyl import __version__
from weyl.core.differ import comparar_archivos_c

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="weyl",
    help="⚖️ WEYL — Herramienta de diffing semántico y comparación estructural AST entre códigos C.",
    add_completion=True,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]WEYL[/bold cyan] versión [bold]{__version__}[/bold]")
        raise typer.Exit(code=0)


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Muestra la versión de WEYL.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


def generar_seccion_markdown(reporte) -> str:
    """Genera sección de comparación semántica y diffing estructural para Dredd."""
    lines = ["## Comparación Semántica con Solución Canónica (Weyl)\n"]
    lines.append(f"- **Archivo estudiante:** `{reporte.archivo_estudiante.name}`")
    lines.append(f"- **Archivo solución modelo:** `{reporte.archivo_modelo.name}`")
    lines.append(f"- **Similitud global:** `{reporte.similitud_global * 100:.1f}%`\n")
    if reporte.similitud_global >= 0.9:
        lines.append("> [!TIP]\n> **Alta Correspondencia Estructural:** La entrega replica fielmente la arquitectura y diseño de la solución modelo.\n")
    else:
        lines.append("> [!NOTE]\n> **Divergencia Estructural:** La entrega presenta funciones adicionales, faltantes o algoritmos diferentes.\n")

    if reporte.funciones:
        lines.append("| Función | Estado | Similitud | Líneas (Est / Mod) | Detalle de Diferencias |")
        lines.append("| :--- | :---: | :---: | :---: | :--- |")
        for d in reporte.funciones:
            cambio_txt = d.cambios[0] if d.cambios else "Sin cambios"
            lines.append(f"| `{d.nombre}()` | **{d.estado}** | {d.similitud * 100:.0f}% | {d.lineas_estudiante} / {d.lineas_modelo} | {cambio_txt} |")
        lines.append("")
    return "\n".join(lines)


@app.command("diff")
@app.command("check")
def diff_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante."),
    modelo: Path = typer.Argument(..., help="Código C de la solución modelo."),
    side_by_side: bool = typer.Option(False, "--side-by-side", "-s", help="Visualizar comparación lado a lado en dos columnas."),
    json_output: bool = typer.Option(False, "--json", help="Salida en formato JSON."),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", "-o", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
) -> None:
    """Compara semánticamente ambos códigos función por función."""
    if not estudiante.is_file():
        err_console.print(f"[red]Error:[/red] No se encontró el archivo del estudiante: '{estudiante}'.")
        raise typer.Exit(code=2)
    if not modelo.is_file():
        err_console.print(f"[red]Error:[/red] No se encontró la solución modelo: '{modelo}'.")
        raise typer.Exit(code=2)

    reporte = comparar_archivos_c(estudiante, modelo)

    if output_md:
        md_text = generar_seccion_markdown(reporte)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[green]✓ Sección Markdown generada en:[/green] [cyan]{output_md}[/cyan]")
        raise typer.Exit(code=0)

    if json_output:
        print(json.dumps(reporte.to_dict(), indent=2, ensure_ascii=False))
        raise typer.Exit(code=0)

    if side_by_side:
        from rich.columns import Columns
        from rich.syntax import Syntax
        c1 = estudiante.read_text(encoding="utf-8", errors="replace")
        c2 = modelo.read_text(encoding="utf-8", errors="replace")
        p1 = Panel(Syntax(c1, "c", line_numbers=True), title=f"Estudiante ({estudiante.name})", border_style="cyan")
        p2 = Panel(Syntax(c2, "c", line_numbers=True), title=f"Modelo ({modelo.name})", border_style="green")
        console.print(Columns([p1, p2]))
        return

    tabla = Table(title=f"Comparación Semántica: {estudiante.name} vs {modelo.name}")
    tabla.add_column("Función", style="bold cyan")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Similitud", justify="right")
    tabla.add_column("Líneas (Est/Mod)", justify="center")
    tabla.add_column("Detalle de Cambios")

    for d in reporte.funciones:
        color = "green" if d.estado == "IDENTICA" else "yellow" if d.estado == "MODIFICADA" else "red" if d.estado == "ELIMINADA" else "blue"
        cambio_txt = d.cambios[0] if d.cambios else "Sin cambios"
        tabla.add_row(
            f"{d.nombre}()",
            f"[{color}]{d.estado}[/{color}]",
            f"{d.similitud * 100:.0f}%",
            f"{d.lineas_estudiante} / {d.lineas_modelo}",
            cambio_txt[:50],
        )

    console.print(tabla)


@app.command("doctor")
def doctor_cmd() -> None:
    """Verifica el estado del entorno de diffing semántico WEYL."""
    tabla = Table(title="🏥 Diagnóstico del Entorno WEYL (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle")

    try:
        import tree_sitter_c
        tabla.add_row("Tree-Sitter C Parser", "[bold green]✓ Operativo[/bold green]", "Gramática C AST disponible")
    except Exception:
        tabla.add_row("Motor Regex/AST", "[bold green]✓ Operativo[/bold green]", "Extractor sintáctico de funciones C activo")

    console.print(tabla)


@app.command("track")
def track_cmd(
    dir_r1: Path = typer.Argument(..., help="Directorio o archivo de la revisión inicial (r1)."),
    dir_r2: Path = typer.Argument(..., help="Directorio o archivo de la reentrega (r2)."),
) -> None:
    """Analiza la evolución semántica y mejoras introducidas entre revisiones sucesivas de un estudiante."""
    if not dir_r1.exists() or not dir_r2.exists():
        err_console.print(f"[red]Error:[/red] No se encontraron una o ambas rutas de revisión: '{dir_r1}', '{dir_r2}'.")
        raise typer.Exit(code=2)

    console.print(f"\n[bold cyan]📈 Seguimiento Evolutivo: {dir_r1.name} ➔ {dir_r2.name}[/bold cyan]\n")

    files_r1 = {f.name: f for f in (dir_r1.glob("*.c") if dir_r1.is_dir() else [dir_r1])}
    files_r2 = {f.name: f for f in (dir_r2.glob("*.c") if dir_r2.is_dir() else [dir_r2])}

    comunes = set(files_r1.keys()) & set(files_r2.keys())
    if not comunes:
        console.print("[yellow]No se encontraron archivos C coincidentes entre ambas revisiones.[/yellow]")
        return

    tabla = Table(title="Evolución de Funciones entre Revisiones")
    tabla.add_column("Archivo / Función", style="bold cyan")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Similitud", justify="right")
    tabla.add_column("Cambios Detectados")

    for fname in sorted(comunes):
        rep = comparar_archivos_c(files_r1[fname], files_r2[fname])
        for fn in rep.funciones:
            color = "green" if fn.estado == "IDENTICA" else "yellow" if fn.estado == "MODIFICADA" else "red"
            cambio_str = fn.cambios[0] if fn.cambios else "Sin cambios estructurales"
            tabla.add_row(f"{fname}::{fn.nombre}()", f"[{color}]{fn.estado}[/{color}]", f"{fn.similitud * 100:.0f}%", cambio_str)

    console.print(tabla)


@app.command("report")
def report_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante."),
    modelo: Path = typer.Argument(..., help="Código C de la solución modelo."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
) -> None:
    """Genera directamente la sección de reporte Markdown de WEYL para Dredd."""
    if not estudiante.is_file() or not modelo.is_file():
        err_console.print(f"[red]Error:[/red] Uno o ambos archivos no existen.")
        raise typer.Exit(code=2)
    reporte = comparar_archivos_c(estudiante, modelo)
    md_content = generar_seccion_markdown(reporte)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[green]✓ Reporte Markdown generado en:[/green] [cyan]{output}[/cyan]")
    else:
        print(md_content)


@app.command("check-api")
def check_api_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante."),
    modelo: Path = typer.Argument(..., help="Código C de la solución modelo."),
) -> None:
    """Verifica que las firmas de funciones respeten los contratos y parámetros de la consigna."""
    from weyl.core.api_checker import comparar_firmas_api
    if not estudiante.is_file() or not modelo.is_file():
        err_console.print(f"[red]Error:[/red] Uno o ambos archivos no existen.")
        raise typer.Exit(code=2)
    discrepancias = comparar_firmas_api(estudiante, modelo, console=console)
    if discrepancias:
        raise typer.Exit(code=1)


@app.command("check-complexity")
def check_complexity_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante."),
    modelo: Path = typer.Argument(..., help="Código C de la solución modelo."),
) -> None:
    """Detecta transformaciones algorítmicas, reducciones de anidación o cambio recursión/iteración."""
    from weyl.core.complexity import auditar_transformaciones_algoritmicas
    if not estudiante.is_file() or not modelo.is_file():
        err_console.print(f"[red]Error:[/red] Uno o ambos archivos no existen.")
        raise typer.Exit(code=2)
    auditar_transformaciones_algoritmicas(estudiante, modelo, console=console)


@app.command("detect-orphans")
def detect_orphans_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante a auditar."),
) -> None:
    """Detecta funciones auxiliares huérfanas o código muerto agregado en la entrega."""
    from weyl.core.orphan_detector import detectar_funciones_huerfanas
    if not estudiante.is_file():
        err_console.print(f"[red]Error:[/red] No se encontró el archivo: '{estudiante}'.")
        raise typer.Exit(code=2)
    detectar_funciones_huerfanas(estudiante, console=console)


@app.command("export-html")
def export_html_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante."),
    modelo: Path = typer.Argument(..., help="Código C de la solución modelo."),
    output: Path = typer.Option(Path("weyl_report.html"), "--output", "-o", help="Ruta de destino del reporte HTML interactivo."),
) -> None:
    """Genera un reporte interactivo en formato HTML con diferencias semánticas."""
    from weyl.core.html_report import generar_html_diff
    if not estudiante.is_file() or not modelo.is_file():
        err_console.print(f"[red]Error:[/red] Uno o ambos archivos no existen.")
        raise typer.Exit(code=2)
    reporte = comparar_archivos_c(estudiante, modelo)
    res = generar_html_diff(reporte, output)
    console.print(f"[bold green]✓ Reporte HTML interactivo generado en:[/bold green] [cyan]{res}[/cyan]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()


