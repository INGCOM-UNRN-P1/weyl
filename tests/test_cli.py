"""Tests de integración de la CLI de WEYL."""

import json
from pathlib import Path
from typer.testing import CliRunner
from weyl.cli import app

runner = CliRunner()


def test_cli_version():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "WEYL" in res.stdout


def test_cli_diff_json(tmp_path):
    f1 = tmp_path / "a.c"
    f2 = tmp_path / "b.c"
    f1.write_text("int f() { return 1; }\n")
    f2.write_text("int f() { return 2; }\n")

    res = runner.invoke(app, ["diff", str(f1), str(f2), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert len(data["diferencias"]) == 1
    assert data["diferencias"][0]["nombre"] == "f"
