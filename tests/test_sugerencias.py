"""`weyl suggest --docente` (QoL #1028)."""

import json

from typer.testing import CliRunner

from weyl.cli import app

runner = CliRunner()
MODELO = """int maximo(int a, int b) { return a > b ? a : b; }
int mayor(const int *v, int n)
{
    int m = v[0];
    for (int i = 1; i < n; i++)
    {
        m = maximo(m, v[i]);
    }
    return m;
}
"""
ENTREGA = """int mayor(const int *v, int n)
{
    int m = v[0];
    for (int i = 0; i < n; i++)
    {
        for (int j = 0; j < n; j++)
        {
            if (v[j] > m)
            {
                m = v[j];
            }
        }
    }
    return m;
}
"""


def test_requiere_docente(tmp_path):
    (tmp_path / "e.c").write_text(ENTREGA, encoding="utf-8")
    (tmp_path / "m.c").write_text(MODELO, encoding="utf-8")
    assert runner.invoke(app, ["suggest", str(tmp_path / "e.c"), str(tmp_path / "m.c")]).exit_code == 2


def test_sugerencias_sin_mostrar_la_solucion(tmp_path):
    (tmp_path / "e.c").write_text(ENTREGA, encoding="utf-8")
    (tmp_path / "m.c").write_text(MODELO, encoding="utf-8")
    res = runner.invoke(app, ["suggest", str(tmp_path / "e.c"), str(tmp_path / "m.c"), "--docente", "--json"])
    datos = json.loads(res.stdout)
    aspectos = {s["aspecto"] for s in datos["sugerencias"]}
    assert {"anidamiento", "modularidad"} <= aspectos
    assert "maximo" not in res.stdout and "a > b" not in res.stdout
