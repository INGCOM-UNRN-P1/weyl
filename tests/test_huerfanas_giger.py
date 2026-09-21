"""Regresión de WEYL-D0902: detect-orphans delega en giger y cae al detector propio."""

import shutil
import subprocess

import pytest

from weyl.core import orphan_detector as od

CODIGO = "int aux(void){return 1;}\nint suma(int a){return a;}\nint main(void){return suma(1);}\n"


@pytest.fixture
def fuente(tmp_path):
    f = tmp_path / "o.c"
    f.write_text(CODIGO)
    return f


def test_delega_en_giger_si_responde(fuente, monkeypatch):
    monkeypatch.setattr(od.shutil, "which", lambda _: "/usr/bin/giger")
    monkeypatch.setattr(od.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a, 0, stdout='{"funciones_huerfanas": ["desde_giger"]}', stderr=""))
    assert od.detectar_funciones_huerfanas(fuente) == ["desde_giger"]


def test_sin_giger_usa_el_detector_propio(fuente, monkeypatch):
    monkeypatch.setattr(od.shutil, "which", lambda _: None)
    assert od.detectar_funciones_huerfanas(fuente) == ["aux"]


def test_salida_inutilizable_de_giger_cae_al_propio(fuente, monkeypatch):
    monkeypatch.setattr(od.shutil, "which", lambda _: "/usr/bin/giger")
    monkeypatch.setattr(od.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a, 2, stdout="no es json", stderr=""))
    assert od.detectar_funciones_huerfanas(fuente) == ["aux"]


@pytest.mark.skipif(shutil.which("giger") is None, reason="giger no instalado")
def test_giger_real_y_detector_propio_coinciden(fuente):
    assert od.detectar_funciones_huerfanas(fuente) == od.detectar_funciones_huerfanas(fuente, usar_giger=False)
