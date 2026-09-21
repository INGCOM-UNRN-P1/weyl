"""Regresión de WEYL-D0401: los comandos de análisis ofrecen --json versionado."""

import json

import typer.main
from typer.testing import CliRunner

from weyl.cli import app

runner = CliRunner()

MODELO = "int suma(int a, int b) { return a + b; }\nint main(void) { return suma(1, 2); }\n"
ESTUDIANTE = "int suma(int x, int y, int z) { return x + y; }\nint aux(void) { return 1; }\nint main(void) { return suma(1, 2, 3); }\n"


def _archivos(tmp_path):
    e, m = tmp_path / "e.c", tmp_path / "m.c"
    e.write_text(ESTUDIANTE)
    m.write_text(MODELO)
    return str(e), str(m)


def _json(res):
    datos = json.loads(res.output)
    assert datos["schema_version"] == "1.0.0"
    assert datos["herramienta"] == "weyl"
    return datos


def test_todos_los_comandos_de_analisis_declaran_json():
    exentos = {"report", "check", "diff"}  # report emite Markdown; diff/check ya lo tenían
    cmd = typer.main.get_command(app)
    sin_json = [n for n, c in cmd.commands.items()
                if n not in exentos and "--json" not in {o for p in c.params for o in getattr(p, "opts", [])}]
    assert not sin_json, f"sin --json: {sin_json}"


def test_check_api_json_y_codigo_de_salida(tmp_path):
    e, m = _archivos(tmp_path)
    res = runner.invoke(app, ["check-api", e, m, "--json"])
    datos = _json(res)
    assert res.exit_code == 1 and datos["ok"] is False
    assert datos["discrepancias"][0]["funcion"] == "suma"


def test_check_complexity_detect_orphans_matrix_ast_diff_track_export(tmp_path):
    e, m = _archivos(tmp_path)
    assert "transformaciones" in _json(runner.invoke(app, ["check-complexity", e, m, "--json"]))
    assert _json(runner.invoke(app, ["detect-orphans", e, "--json"]))["huerfanas"] == ["aux"]
    assert "suma" in _json(runner.invoke(app, ["matrix", e, m, "--json"]))["matriz"]
    estados = {f["funcion"]: f["estado"] for f in _json(runner.invoke(app, ["ast-diff", e, m, "--json"]))["funciones"]}
    assert estados["aux"] == "AGREGADA" and estados["suma"] == "COMUN"
    assert _json(runner.invoke(app, ["track", e, m, "--json"]))["archivos"] == []
    salida = tmp_path / "r.html"
    assert _json(runner.invoke(app, ["export-html", e, m, "-o", str(salida), "--json"]))["salida"] == str(salida.resolve())
    assert _json(runner.invoke(app, ["doctor", "--json"]))["ok"] is True
    res = runner.invoke(app, ["check-plagiarism", e, e, "--json"])
    assert res.exit_code == 1 and _json(res)["sospechoso"] is True


def test_track_json_con_archivos_comunes(tmp_path):
    a, b = tmp_path / "r1", tmp_path / "r2"
    a.mkdir(); b.mkdir()
    (a / "p.c").write_text(MODELO)
    (b / "p.c").write_text(ESTUDIANTE)
    archivos = _json(runner.invoke(app, ["track", str(a), str(b), "--json"]))["archivos"]
    assert archivos[0]["archivo"] == "p.c" and archivos[0]["funciones"]
