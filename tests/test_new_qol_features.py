"""Tests para las nuevas features QoL de WEYL: check-api, check-complexity, detect-orphans, export-html."""

from pathlib import Path
from typer.testing import CliRunner
from weyl.cli import app
from weyl.core.api_checker import comparar_firmas_api
from weyl.core.complexity import auditar_transformaciones_algoritmicas
from weyl.core.orphan_detector import detectar_funciones_huerfanas
from weyl.core.html_report import generar_html_diff
from weyl.core.differ import comparar_archivos_c

runner = CliRunner()


def test_weyl_check_api_signatures_match(tmp_path: Path):
    mod = tmp_path / "mod.c"
    est = tmp_path / "est.c"
    mod.write_text("int suma(int a, int b) { return a + b; }\n")
    est.write_text("int suma(int a, int b) { return a + b; }\n")

    discrepancias = comparar_firmas_api(est, mod)
    assert len(discrepancias) == 0


def test_weyl_check_api_signatures_mismatch(tmp_path: Path):
    mod = tmp_path / "mod.c"
    est = tmp_path / "est.c"
    mod.write_text("int suma(int a, int b) { return a + b; }\nvoid reset(void) {}\n")
    est.write_text("double suma(int a) { return a; }\n")

    discrepancias = comparar_firmas_api(est, mod)
    assert len(discrepancias) >= 1
    funcs = [d["funcion"] for d in discrepancias]
    assert "reset" in funcs or "suma" in funcs


def test_weyl_complexity_analysis(tmp_path: Path):
    mod = tmp_path / "mod.c"
    est = tmp_path / "est.c"
    # Modelo recursivo vs estudiante iterativo
    mod.write_text("int fact(int n) { if (n <= 1) return 1; return n * fact(n - 1); }\n")
    est.write_text("int fact(int n) { int res = 1; for (int i = 1; i <= n; i++) res *= i; return res; }\n")

    transformaciones = auditar_transformaciones_algoritmicas(est, mod)
    assert len(transformaciones) >= 1
    assert any("Recursión → Iteración" in t["tipo"] for t in transformaciones)


def test_weyl_orphan_function_detection(tmp_path: Path):
    est = tmp_path / "est.c"
    est.write_text("""
void auxiliar_inutil(void) { }
int main(void) { return 0; }
""")
    huerfanas = detectar_funciones_huerfanas(est)
    assert "auxiliar_inutil" in huerfanas


def test_weyl_html_export(tmp_path: Path):
    mod = tmp_path / "mod.c"
    est = tmp_path / "est.c"
    out_html = tmp_path / "reporte.html"
    mod.write_text("int foo(void) { return 1; }\n")
    est.write_text("int foo(void) { return 2; }\n")

    reporte = comparar_archivos_c(est, mod)
    res = generar_html_diff(reporte, out_html)
    assert res.is_file()
    txt = res.read_text(encoding="utf-8")
    assert "Reporte de Comparación Semántica" in txt
    assert "foo" in txt
