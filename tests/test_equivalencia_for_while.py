"""Regresión de WEYL-D0304: for/while equivalentes solo si el `for` desazucara al `while`."""

from weyl.core.alpha_equiv import desazucarar_for_a_while, detectar_equivalencia_for_while

FOR = "for (int i = 0; i < 10; i++) { printf(\"%d\", i); }"
WHILE = "int i = 0; while (i < 10) { printf(\"%d\", i); i++; }"


def test_for_y_su_while_equivalente():
    assert detectar_equivalencia_for_while(FOR, WHILE) is True
    assert detectar_equivalencia_for_while(WHILE, FOR) is True


def test_mismos_operadores_pero_otra_logica_no_es_equivalente():
    # Mismos operadores (<, ++) que la versión anterior comparaba como bolsa.
    otro = "int j = 5; while (j < 20) { suma += j * 2; j++; }"
    assert detectar_equivalencia_for_while(FOR, otro) is False


def test_paso_distinto_no_es_equivalente():
    assert detectar_equivalencia_for_while(FOR, WHILE.replace("i++", "i += 2")) is False


def test_cota_distinta_no_es_equivalente():
    assert detectar_equivalencia_for_while(FOR, WHILE.replace("10", "11")) is False


def test_for_anidado_se_desazucara_completo():
    codigo = "for (i = 0; i < n; i++) { for (j = 0; j < m; j++) { f(i, j); } }"
    assert "for" not in desazucarar_for_a_while(codigo)


def test_dos_for_no_se_declaran_equivalentes_a_si_mismos():
    assert detectar_equivalencia_for_while(FOR, FOR) is False
