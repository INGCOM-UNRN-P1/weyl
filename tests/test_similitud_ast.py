"""Matriz de similitud de un lote sobre el AST (Ola 48): resiste renombrar y reordenar."""

import json
import random
import re

import pytest
from typer.testing import CliRunner

from weyl.cli import app
from weyl.core.similitud_ast import (
    Huellero,
    comparar_lote,
    contencion,
    dice,
    entregas_de_directorio,
    matriz_csv,
)

ORIGINAL = """#include <stdio.h>
#include <stdlib.h>

typedef struct nodo { int valor; struct nodo *sig; } nodo_t;

int suma(const int *v, int n)
{
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += v[i];
    }
    return total;
}

int maximo(const int *v, int n)
{
    int m = v[0];
    for (int i = 1; i < n; i++) {
        if (v[i] > m) {
            m = v[i];
        }
    }
    return m;
}

nodo_t *agregar(nodo_t *cabeza, int valor)
{
    nodo_t *nuevo = malloc(sizeof(nodo_t));
    if (nuevo == NULL) {
        return cabeza;
    }
    nuevo->valor = valor;
    nuevo->sig = cabeza;
    return nuevo;
}

void liberar(nodo_t *cabeza)
{
    while (cabeza != NULL) {
        nodo_t *sig = cabeza->sig;
        free(cabeza);
        cabeza = sig;
    }
}

int main(void)
{
    int v[3] = {1, 2, 3};
    printf("%d %d\\n", suma(v, 3), maximo(v, 3));
    return 0;
}
"""

DISTINTO = """#include <stdio.h>
#include <string.h>

static int es_palindromo(const char *s)
{
    size_t a = 0, b = strlen(s);
    while (a + 1 < b) {
        b--;
        if (s[a] != s[b]) {
            return 0;
        }
        a++;
    }
    return 1;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "uso\\n");
        return 1;
    }
    puts(es_palindromo(argv[1]) ? "si" : "no");
    return 0;
}
"""

RENOMBRES = {
    "nodo": "celda", "nodo_t": "celda_t", "valor": "dato", "sig": "proxima", "suma": "acumular",
    "maximo": "mayor", "agregar": "insertar", "liberar": "destruir", "cabeza": "lista", "total": "s",
    "nuevo": "p", "v": "arr", "n": "largo", "i": "k", "m": "best",
}


def renombrar(codigo: str) -> str:
    return re.sub(r"\b[a-z_]+\b", lambda m: RENOMBRES.get(m.group(0), m.group(0)), codigo)


def funciones_de(codigo: str) -> tuple[str, list[str]]:
    """El encabezado y las definiciones de primer nivel, para reordenarlas."""
    encabezado, *resto = re.split(r"\n\n(?=[a-z])", codigo.split("\n\n", 1)[1])
    return codigo.split("\n\n", 1)[0] + "\n\n" + encabezado, resto


def reordenar(codigo: str, semilla: int) -> str:
    encabezado, definiciones = funciones_de(codigo)
    random.Random(semilla).shuffle(definiciones)
    return encabezado + "\n\n" + "\n\n".join(definiciones)


def similitud(a: str, b: str) -> float:
    huellero = Huellero()
    return dice(huellero.huella([a]).bolsa, huellero.huella([b]).bolsa)


def test_renombrar_todo_no_cambia_nada():
    assert renombrar(ORIGINAL) != ORIGINAL
    assert similitud(ORIGINAL, renombrar(ORIGINAL)) == 100.0


@pytest.mark.parametrize("semilla", range(5))
def test_reordenar_funciones_no_cambia_nada(semilla):
    otra = reordenar(ORIGINAL, semilla)
    assert similitud(ORIGINAL, otra) == 100.0
    assert similitud(ORIGINAL, renombrar(otra)) == 100.0


@pytest.mark.parametrize("original, disfraz", [
    ("int total = 0;", "/* acumulador */ int total = 0; // arranca en cero"),
    ('"%d %d\\n"', '"resultado: %d y %d\\n"'),
    ("int total = 0;", "long total = 0;"),
    ("const int *v, int n)\n{\n    int total", "int *v, int n)\n{\n    int total"),
    ("if (nuevo == NULL) {\n        return cabeza;\n    }", "if (nuevo == NULL)\n        return cabeza;"),
    ("return total;", "return (total);"),
    ("i++", "++i"),
])
def test_lo_cosmetico_no_cuenta(original, disfraz):
    assert original in ORIGINAL
    assert similitud(ORIGINAL, ORIGINAL.replace(original, disfraz)) == 100.0


def test_los_prototipos_no_cuentan():
    con_prototipos = ORIGINAL.replace("int suma(const", "int suma(const int *v, int n);\nint maximo(const int *v, int n);\n\nint suma(const", 1)
    assert similitud(ORIGINAL, con_prototipos) == 100.0


def test_un_cambio_en_una_funcion_no_arrastra_a_las_demas():
    # Con formas de texto ordenadas, tocar una función la mueve de lugar y desalinea la comparación.
    otra = ORIGINAL.replace("if (v[i] > m) {\n            m = v[i];\n        }", "m = v[i] > m ? v[i] : m;")
    assert 80.0 <= similitud(ORIGINAL, otra) < 100.0


def test_un_for_reescrito_como_while_sigue_siendo_muy_parecido():
    otra = ORIGINAL.replace(
        "for (int i = 0; i < n; i++) {\n        total += v[i];\n    }",
        "int i = 0;\n    while (i < n) {\n        total += v[i];\n        i++;\n    }",
    )
    assert similitud(ORIGINAL, otra) >= 85.0


def test_programas_distintos_quedan_lejos():
    assert similitud(ORIGINAL, DISTINTO) < 30.0


def test_las_llamadas_a_la_biblioteca_distinguen():
    a = "void f(int *p) { free(p); free(p); free(p); }"
    assert similitud(a, a.replace("free", "liberar_todo")) < 100.0
    propia = "void g(int *p) { }\nvoid f(int *p) { g(p); g(p); }"
    assert similitud(propia, propia.replace("g(", "h(")) == 100.0


def test_un_puntero_a_funcion_llamado_es_propio():
    # Apareció en el banco: `predicado(arr[i])` llama a un parámetro, no a la biblioteca.
    a = "int contar(const int *v, int n, int (*pred)(int)) { int c = 0; if (pred(v[0]) && pred(v[n])) { c = 1; } return c; }"
    assert similitud(a, a.replace("pred", "criterio")) == 100.0
    typedef = "typedef int (*p_t)(int);\nint f(int x, p_t op) { return op(x) + op(x + 1); }"
    assert similitud(typedef, typedef.replace("op", "funcion")) == 100.0


def test_una_entrega_de_varios_archivos_es_un_programa():
    # `suma` está en otro archivo: en main sigue siendo una función propia, no de biblioteca.
    a = "int main(void) { return suma(1, 2) + suma(3, 4); }"
    b = "int suma(int x, int y) { return x + y; }"
    huellero = Huellero()
    junta = huellero.huella([a, b])
    renombrada = huellero.huella([a.replace("suma", "add"), b.replace("suma", "add")])
    assert dice(junta.bolsa, renombrada.bolsa) == 100.0


def test_una_expresion_muy_profunda_no_rompe():
    profunda = "int f(int a) { return " + " + ".join(["a"] * 3000) + "; }"
    assert similitud(profunda, profunda) == 100.0


def test_codigo_roto_no_rompe():
    assert Huellero().huella(["int f( { if while ) ]"]).total >= 0
    assert Huellero().huella([""]).total == 0


def test_contencion_ve_la_copia_con_codigo_agregado():
    huellero = Huellero()
    a = huellero.huella([ORIGINAL]).bolsa
    b = huellero.huella([ORIGINAL + DISTINTO.split("\n\n", 1)[1].replace("main", "relleno")]).bolsa
    assert contencion(a, b) == 100.0 > dice(a, b)


def _curso(tmp_path):
    for nombre, codigo in (("ana", ORIGINAL), ("beto", renombrar(reordenar(ORIGINAL, 1))), ("carla", DISTINTO)):
        (tmp_path / nombre).mkdir()
        (tmp_path / nombre / "main.c").write_text(codigo, encoding="utf-8")
    (tmp_path / "dani").mkdir()
    (tmp_path / "dani" / "notas.txt").write_text("sin código", encoding="utf-8")
    return tmp_path


def test_el_lote_da_la_matriz_completa_y_los_grupos(tmp_path):
    datos = comparar_lote(entregas_de_directorio(_curso(tmp_path)), umbral=90)
    assert sorted(datos["matriz"]) == ["ana", "beto", "carla"]
    assert datos["matriz"]["ana"]["beto"] == datos["matriz"]["beto"]["ana"] == 100.0
    assert datos["matriz"]["ana"]["carla"] < 30.0 and datos["matriz"]["carla"]["carla"] == 100.0
    assert [g["entregas"] for g in datos["grupos"]] == [["ana", "beto"]]
    assert {(f["a"], f["b"]) for f in datos["pares"][0]["funciones"]} >= {("suma", "acumular"), ("liberar", "destruir")}


def test_el_lote_no_guarda_codigo(tmp_path):
    texto = json.dumps(comparar_lote(entregas_de_directorio(_curso(tmp_path))), ensure_ascii=False)
    assert "total" not in texto and "malloc" not in texto


def test_la_plantilla_se_descuenta_aunque_la_renombren(tmp_path):
    catedra = "int leer_entero(void) { int x = 0; if (scanf(\"%d\", &x) != 1) { return -1; } return x; }\n"
    (tmp_path / "plantilla.c").write_text(catedra, encoding="utf-8")
    a = tmp_path / "a.c"
    b = tmp_path / "b.c"
    a.write_text(catedra + "int doble(int x) { return x * 2 + 1 - 1; }\n", encoding="utf-8")
    b.write_text(catedra.replace("leer_entero", "pedir").replace("x", "y") + DISTINTO, encoding="utf-8")
    entregas = {"a": [a], "b": [b]}
    assert comparar_lote(entregas, plantilla=tmp_path / "plantilla.c")["matriz"]["a"]["b"] \
        < comparar_lote(entregas)["matriz"]["a"]["b"]
    solo = tmp_path / "solo.c"
    solo.write_text(catedra, encoding="utf-8")
    assert comparar_lote({"solo": [solo]}, plantilla=tmp_path / "plantilla.c")["sin_codigo"] == ["solo"]


def _sobre_plantilla(tmp_path):
    """Seis entregas sobre el mismo código común: dos se copian y una no agregó nada."""
    comun = "\n".join(f"int auxiliar_{i}(int x) {{ if (x > {i}) {{ x = x * {i} + 1; }} return x; }}" for i in range(20))
    propios = {
        "ana": "int f(int *v, int n) { int t = 0; for (int i = 0; i < n; i++) { if (v[i] > 0) { t += v[i] * 2; } } return t; }",
        "caro": "int g(char *s) { int n = 0; while (s[n] != 0) { if (s[n] == 32) { n += 2; } else { n++; } } return n; }",
        "dani": "double h(double a, double b) { double c = a / b; return c * c - a + b * (a - 1.5); }",
        "eli": "void k(int **m, int f) { for (int i = 0; i < f; i++) { free(m[i]); m[i] = NULL; } free(m); }",
        "fede": "",
    }
    propios["beto"] = propios["ana"].replace("t", "acc").replace("inacc", "int").replace("reaccurn", "return")
    entregas = {}
    for nombre, propio in propios.items():
        archivo = tmp_path / f"{nombre}.c"
        archivo.write_text(comun + "\n" + propio + "\n", encoding="utf-8")
        entregas[nombre] = [archivo]
    return entregas


def test_lo_comun_a_la_mayoria_no_cuenta(tmp_path):
    entregas = _sobre_plantilla(tmp_path)
    crudo = comparar_lote(entregas, comunes=0)
    assert crudo["subarboles_comunes"] == 0 and len(crudo["pares"]) > 1
    datos = comparar_lote(entregas)
    assert datos["subarboles_comunes"] > 0
    assert [g["entregas"] for g in datos["grupos"]] == [["ana", "beto"]]
    assert datos["matriz"]["ana"]["caro"] < 30.0


def test_quien_no_agrego_nada_queda_sin_codigo_propio(tmp_path):
    datos = comparar_lote(_sobre_plantilla(tmp_path))
    assert datos["sin_codigo"] == ["fede"] and "fede" not in datos["matriz"]


def test_en_un_lote_chico_no_se_descuenta_lo_comun(tmp_path):
    entregas = _sobre_plantilla(tmp_path)
    datos = comparar_lote({n: entregas[n] for n in ("ana", "beto", "caro")})
    assert datos["subarboles_comunes"] == 0 and datos["matriz"]["ana"]["beto"] == 100.0


def test_los_c_sueltos_tambien_son_entregas_y_lo_oculto_no(tmp_path):
    (tmp_path / "ana.c").write_text(ORIGINAL, encoding="utf-8")
    (tmp_path / "_baseline").mkdir()
    (tmp_path / "_baseline" / "x.c").write_text(ORIGINAL, encoding="utf-8")
    (tmp_path / "beto" / ".git").mkdir(parents=True)
    (tmp_path / "beto" / ".git" / "x.c").write_text(ORIGINAL, encoding="utf-8")
    assert sorted(entregas_de_directorio(tmp_path)) == ["ana"]


def test_el_csv_tiene_una_fila_y_una_columna_por_entrega():
    assert matriz_csv({"a": {"a": 100.0, "b": 12.5}, "b": {"a": 12.5, "b": 100.0}}) == (
        "entrega,a,b\na,100.0,12.5\nb,12.5,100.0\n"
    )


def test_cli_cohort(tmp_path):
    (tmp_path / "curso").mkdir()
    curso = _curso(tmp_path / "curso")
    csv = tmp_path / "salida" / "matriz.csv"
    res = CliRunner().invoke(app, ["cohort", str(curso), "--json", "--csv", str(csv)])
    assert res.exit_code == 0, res.output
    assert json.loads(res.output)["grupos"][0]["entregas"] == ["ana", "beto"]
    assert csv.read_text(encoding="utf-8").startswith("entrega,ana,beto,carla\n")
    res = CliRunner().invoke(app, ["cohort", str(curso)], env={"COLUMNS": "150"})
    assert res.exit_code == 0 and "ana, beto" in res.output
