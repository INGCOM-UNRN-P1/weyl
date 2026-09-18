"""Regresión de WEYL-D0302/D0303.

D0302: `detectar_inversion_if_else` terminaba en un `return True` incondicional,
así que cualquier par de ramas cruzadas se declaraba equivalente aunque las
condiciones no tuvieran relación (similitud inflada a 0.90).
D0303: `_eliminar_comentarios` recortaba desde el `//` de una URL dentro de un
string, y una llave dentro de un literal descuadraba el contador del extractor.
"""

import pytest

from weyl.core.alpha_equiv import detectar_inversion_if_else
from weyl.core.differ import _eliminar_comentarios, _extraer_mapa_funciones


def test_condiciones_sin_relacion_no_son_equivalentes():
    """El caso exacto del hallazgo: x>5 vs y<100 con ramas cruzadas."""
    a = "if(x>5){return 1;}else{return 2;}"
    b = "if(y<100){return 2;}else{return 1;}"
    assert detectar_inversion_if_else(a, b) is False


@pytest.mark.parametrize(
    "a, b",
    [
        ("if(x>5){return 1;}else{return 2;}", "if(y<=5){return 2;}else{return 1;}"),
        ("if(a==b){return 1;}else{return 2;}", "if(c!=d){return 2;}else{return 1;}"),
        ("if(ok){return 1;}else{return 2;}", "if(!ok){return 2;}else{return 1;}"),
    ],
)
def test_la_negacion_real_si_es_equivalente(a, b):
    assert detectar_inversion_if_else(a, b) is True


def test_ramas_distintas_no_son_equivalentes():
    a = "if(x>5){return 1;}else{return 2;}"
    b = "if(y<=5){return 3;}else{return 1;}"
    assert detectar_inversion_if_else(a, b) is False


def test_una_url_en_un_literal_no_se_recorta():
    limpio = _eliminar_comentarios('printf("http://ejemplo"); // comentario real\n')
    assert 'http://ejemplo' in limpio
    assert "comentario real" not in limpio


def test_los_comentarios_de_bloque_se_siguen_eliminando():
    assert "oculto" not in _eliminar_comentarios("int a; /* oculto */ int b;")


def test_una_llave_dentro_de_un_literal_no_rompe_la_extraccion():
    fuente = 'int f(void) {\n  puts("}");\n  return 1;\n}\nint g(void) { return 2; }\n'
    funciones = _extraer_mapa_funciones(fuente)
    assert set(funciones) == {"f", "g"}
    assert "return 1" in funciones["f"]
