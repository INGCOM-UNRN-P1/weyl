"""Tests adicionales para maximizar la cobertura en WEYL."""

import json
from pathlib import Path
from typer.testing import CliRunner
import weyl.cli
from weyl.cli import app
from weyl.core.differ import comparar_archivos_c
from weyl.ripley_plugin import WeylPlugin

runner = CliRunner()


def test_plugin_execution(tmp_path):
    p = WeylPlugin()
    assert p.is_available() is True

    # Empty workspace
    res_empty = p.execute(tmp_path, {})
    assert res_empty["ok"] is True

    # Workspace with canonical and student files
    canon = tmp_path / "canon.c"
    canon.write_text("int f(int a) { return a + 1; }\nvoid obligatoria() {}\n")
    alumno = tmp_path / "student.c"
    alumno.write_text("int f(int a) { return a + 2; }\n")

    res = p.execute(tmp_path, {"solution_path": str(canon)})
    assert res["ok"] is False
    assert len(res["observaciones"]) == 1


def test_cli_diff_rich_output(tmp_path):
    f_a = tmp_path / "a.c"
    f_a.write_text("int suma(int a, int b) { return a + b; }\nvoid extra() {}\n")
    f_b = tmp_path / "b.c"
    f_b.write_text("int suma(int a, int b) { int r = a + b; return r; }\nint faltante() { return 1; }\n")

    res = runner.invoke(app, ["diff", str(f_a), str(f_b)])
    assert res.exit_code == 0
    assert "Comparación Semántica" in res.stdout


def test_cli_file_not_found():
    res = runner.invoke(app, ["diff", "/no/a.c", "/no/b.c"])
    assert res.exit_code == 2


def test_cli_main_block(monkeypatch):
    monkeypatch.setattr("sys.argv", ["weyl", "--version"])
    try:
        weyl.cli.main()
    except SystemExit as e:
        assert e.code == 0
