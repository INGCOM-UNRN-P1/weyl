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


@app.command("diff")
def diff_cmd(
    estudiante: Path = typer.Argument(..., help="Código C del estudiante."),
    modelo: Path = typer.Argument(..., help="Código C de la solución modelo."),
    json_output: bool = typer.Option(False, "--json", help="Salida en formato JSON."),
) -> None:
    """Compara semánticamente ambos códigos función por función."""
    if not estudiante.is_file():
        err_console.print(f"[red]Error:[/red] No se encontró el archivo del estudiante: '{estudiante}'.")
        raise typer.Exit(code=2)
    if not modelo.is_file():
        err_console.print(f"[red]Error:[/red] No se encontró la solución modelo: '{modelo}'.")
        raise typer.Exit(code=2)

    reporte = comparar_archivos_c(estudiante, modelo)

    if json_output:
        print(json.dumps(reporte.to_dict(), indent=2, ensure_ascii=False))
        raise typer.Exit(code=0)

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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
