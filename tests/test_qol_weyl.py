"""Pruebas unitarias de las funcionalidades QoL implementadas en WEYL."""

from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from weyl.cli import app
from weyl.core.alpha_equiv import (
    detectar_equivalencia_for_while,
    detectar_inversion_if_else,
    normalizar_alpha_equivalencia,
)
from weyl.core.ast_analyzer import (
    analizar_estilo_control_flujo,
    auditar_estructuras_intermedias,
    calcular_distancia_edicion,
    detectar_recursion_con_acumulador,
    generar_arbol_ast_diff,
    mapear_llamadas_libc_vs_propias,
)
from weyl.core.differ import comparar_archivos_c
from weyl.core.matrix import calcular_matriz_similitud
from weyl.core.project_differ import (
    auditar_gestion_memoria_revisiones,
    comparar_directorios_modulares,
)

runner = CliRunner()


def test_alpha_equivalence_normalization():
    c1 = "int suma(int a, int b) { int total = a + b; return total; }"
    c2 = "int suma(int x, int y) { int resultado = x + y; return resultado; }"
    n1 = normalizar_alpha_equivalencia(c1)
    n2 = normalizar_alpha_equivalencia(c2)
    assert n1 == n2


def test_inversion_if_else_negada():
    c1 = "if (x > 0) { printf(\"positivo\"); } else { printf(\"no positivo\"); }"
    c2 = "if (x <= 0) { printf(\"no positivo\"); } else { printf(\"positivo\"); }"
    assert detectar_inversion_if_else(c1, c2) is True


def test_equivalencia_for_while():
    c1 = "for (int i = 0; i < 10; i++) { printf(\"%d\", i); }"
    c2 = "int i = 0; while (i < 10) { printf(\"%d\", i); i++; }"
    assert detectar_equivalencia_for_while(c1, c2) is True


def test_calcular_distancia_edicion():
    c1 = "int duplicar(int n) { return n * 2; }"
    c2 = "int duplicar(int x) { return x * 2; }"
    dist = calcular_distancia_edicion(c1, c2)
    assert dist == 0.0


def test_detectar_recursion_con_acumulador():
    c_simple = "int factorial(int n) { if (n <= 1) return 1; return n * factorial(n - 1); }"
    c_tail = "int factorial_helper(int n, int acc) { if (n <= 1) return acc; return factorial_helper(n - 1, n * acc); }"
    res = detectar_recursion_con_acumulador(c_simple, c_tail, "factorial_helper")
    assert res["es_recursiva_modelo"] is True
    assert res["transformacion_acumulador"] is True


def test_analizar_estilo_control_flujo():
    c_guard = """
    void procesar(int x) {
        if (x < 0) return;
        if (x == 0) return;
        printf("%d", x);
    }
    """
    res = analizar_estilo_control_flujo(c_guard)
    assert "Guard Clauses" in res["estilo_predominante"]


def test_mapear_llamadas_libc():
    codigo = """
    #include <stdio.h>
    #include <stdlib.h>
    void ordenar(int *v, size_t n) {
        qsort(v, n, sizeof(int), cmp);
    }
    """
    mapa = mapear_llamadas_libc_vs_propias(codigo)
    assert "qsort" in mapa["libc"]


def test_auditar_estructuras_intermedias():
    c_heap = "int* clonar(int *v, int n) { int *p = malloc(n * sizeof(int)); return p; }"
    c_inplace = "void reverse(int *v, int n) { for(int i=0; i<n/2; i++) { int t=v[i]; v[i]=v[n-1-i]; v[n-1-i]=t; } }"
    assert auditar_estructuras_intermedias(c_heap)["usa_heap"] is True
    assert auditar_estructuras_intermedias(c_inplace)["modo_memoria"] == "Algoritmo In-Place (Sin Memoria Intermedia)"


def test_cli_ast_diff(tmp_path: Path):
    f1 = tmp_path / "f1.c"
    f2 = tmp_path / "f2.c"
    f1.write_text("int f(int a) { return a + 1; }\n", encoding="utf-8")
    f2.write_text("int f(int b) { return b + 2; }\n", encoding="utf-8")
    res = runner.invoke(app, ["ast-diff", str(f1), str(f2)])
    assert res.exit_code == 0
    assert "AST Diff" in res.output


def test_cli_matrix(tmp_path: Path):
    f1 = tmp_path / "a.c"
    f2 = tmp_path / "b.c"
    f1.write_text("int f1(int x) { return x; }\nint f2(int y) { return y * 2; }\n", encoding="utf-8")
    f2.write_text("int g1(int z) { return z; }\n", encoding="utf-8")
    res = runner.invoke(app, ["matrix", str(f1), str(f2)])
    assert res.exit_code == 0
    assert "Matriz Cruzada" in res.output


def test_cli_diff_project(tmp_path: Path):
    d1 = tmp_path / "p1"
    d2 = tmp_path / "p2"
    d1.mkdir()
    d2.mkdir()
    (d1 / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    (d2 / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    res = runner.invoke(app, ["diff-project", str(d1), str(d2), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["similitud_promedio_pct"] == 100.0


def test_cli_audit_memory(tmp_path: Path):
    r1 = tmp_path / "r1.c"
    r2 = tmp_path / "r2.c"
    r1.write_text("void f(void) { char *p = malloc(10); }\n", encoding="utf-8")
    r2.write_text("void f(void) { char *p = malloc(10); free(p); }\n", encoding="utf-8")
    res = runner.invoke(app, ["audit-memory", str(r1), str(r2), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["mejora_balance"] is True


def test_cli_check_plagiarism(tmp_path: Path):
    e1 = tmp_path / "e1.c"
    e2 = tmp_path / "e2.c"
    e1.write_text("int foo(int a, int b) { return a + b; }\n", encoding="utf-8")
    e2.write_text("int bar(int x, int y) { return x + y; }\n", encoding="utf-8")
    res = runner.invoke(app, ["check-plagiarism", str(e1), str(e2), "--threshold", "95.0"])
    assert res.exit_code == 1
    assert "Alta probabilidad de copia" in res.output
