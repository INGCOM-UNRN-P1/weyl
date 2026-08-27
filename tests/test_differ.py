"""Tests unitarios para el motor de diffing semántico de WEYL."""

from pathlib import Path
import pytest
from weyl.core.differ import comparar_archivos_c


def test_comparar_funciones_identicas_y_modificadas(tmp_path):
    f_est = tmp_path / "estudiante.c"
    f_est.write_text("""
    int suma(int a, int b) {
        return a + b;
    }
    int resta(int a, int b) {
        return a - b;
    }
    """)

    f_mod = tmp_path / "modelo.c"
    f_mod.write_text("""
    int suma(int a, int b) {
        return a + b;
    }
    int multiplicacion(int a, int b) {
        return a * b;
    }
    """)

    rep = comparar_archivos_c(f_est, f_mod)
    assert rep.total_funciones_estudiante == 2
    assert rep.total_funciones_modelo == 2

    diff_map = {d.nombre: d.estado for d in rep.funciones}
    assert diff_map["suma"] == "IDENTICA"
    assert diff_map["resta"] == "AGREGADA"
    assert diff_map["multiplicacion"] == "ELIMINADA"
