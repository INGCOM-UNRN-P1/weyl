"""Matriz de similitud de un lote de entregas sobre el AST (tree-sitter).

Cada entrega se reduce a una bolsa de subárboles. Cada subárbol recibe un número por su forma, con
identidad exacta (hash-consing: dos subárboles tienen el mismo número sólo si son iguales), y la
similitud de dos entregas es el coeficiente de Dice de sus bolsas.

- **Renombrar no cambia nada:** los identificadores propios son todos `id`. Las llamadas a funciones
  de biblioteca (`malloc`, `printf`) conservan el nombre, porque no son decisión de quien escribe y
  distinguen programas. De biblioteca es lo que sólo aparece como destino de una llamada: un
  parámetro puntero a función se llama, pero también se declara, y su nombre no cuenta.
- **Reordenar funciones no cambia nada:** una bolsa no tiene orden. No hay que emparejar funciones
  ni ordenar texto, y un cambio chico en una función no mueve la comparación de las demás.
- **Tampoco cuentan:** comentarios, `#include`, prototipos, formato, el texto de cadenas y el valor
  de números, los tipos primitivos, `const`/`static`, los paréntesis y las llaves de un bloque de
  una sola sentencia. `for` y `while` comparten etiqueta y sus cuerpos coinciden.

Lo que sí cambia la medida: mover sentencias dentro de una función, partirla en dos o reescribir una
expresión (`x > y` por `y < x`). Sólo se pierden los subárboles que contienen el cambio.

Lo que comparte la mayoría de un lote no distingue a nadie: es la plantilla, o lo que la consigna
obliga a escribir. Por eso los subárboles presentes en al menos la mitad de las entregas se descuentan
antes de comparar, aunque no se indique una plantilla. En las cohortes de 2026, un TP sobre plantilla
daba una mediana de 95 % sin este descuento y de 7 % con él, y los pares realmente parecidos seguían
arriba de 95 %. Si más de la mitad del curso comparte una copia, este descuento la esconde.

Una similitud alta es un indicio para mirar a mano, no una prueba de copia.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import tree_sitter_c
from tree_sitter import Language, Node, Parser

MOTOR = "weyl-ast"

# Los subárboles más chicos (`i++`, `return 0;`) aparecen en cualquier programa: no distinguen.
TAMANIO_MINIMO = 4

# Fracción de las entregas a partir de la cual un subárbol se considera común a la cohorte.
COMUNES = 0.5
# Con menos entregas, «la mayoría» son dos o tres personas: una copia entre ellas se borraría sola.
ENTREGAS_MINIMAS_PARA_COMUNES = 4

_OMITIDOS = {"comment", "preproc_include", "type_qualifier", "storage_class_specifier"}
_ETIQUETAS = {
    "identifier": "id",
    "field_identifier": "id",
    "type_identifier": "id",
    "statement_identifier": "id",
    "for_statement": "bucle",
    "while_statement": "bucle",
}
# Hojas: no se baja a sus hijos, así el contenido no cuenta.
_HOJAS = {
    "number_literal": "numero",
    "string_literal": "cadena",
    "concatenated_string": "cadena",
    "char_literal": "caracter",
    "primitive_type": "tipo",
    "sized_type_specifier": "tipo",
}
_CON_OPERADOR = {"binary_expression", "assignment_expression", "update_expression", "unary_expression",
                 "pointer_expression"}
# Con un solo hijo no agregan estructura: `if (x) { y; }` es `if (x) y;` y `(a)` es `a`.
_TRANSPARENTES = {"compound_statement", "parenthesized_expression"}

_parser: Optional[Parser] = None


def _analizador() -> Parser:
    global _parser
    if _parser is None:
        _parser = Parser(Language(tree_sitter_c.language()))
    return _parser


def _es_prototipo(nodo: Node) -> bool:
    """`int f(int x);`: declarar o no los prototipos no cambia el programa."""
    if nodo.type != "declaration":
        return False
    pendientes = list(nodo.children)
    while pendientes:
        hijo = pendientes.pop()
        if hijo.type == "function_declarator":
            return True
        if hijo.type in ("pointer_declarator", "parenthesized_declarator"):
            pendientes.extend(hijo.children)
    return False


def _nombres_propios(raiz: Node) -> Set[str]:
    """Todo identificador que aparece fuera de la posición de función de una llamada."""
    propios: Set[str] = set()
    pila = [raiz]
    while pila:
        nodo = pila.pop()
        if nodo.type == "identifier" and nodo.text:
            padre = nodo.parent
            llamado = padre is not None and padre.type == "call_expression" \
                and padre.child_by_field_name("function") == nodo
            if not llamado:
                propios.add(nodo.text.decode("utf-8", errors="replace"))
        pila.extend(nodo.named_children)
    return propios


def _nombre_de_funcion(definicion: Node) -> Optional[str]:
    """El nombre de una `function_definition`, a través de sus declaradores."""
    nodo = definicion.child_by_field_name("declarator")
    while nodo is not None and nodo.type != "identifier":
        nodo = nodo.child_by_field_name("declarator")
    return nodo.text.decode("utf-8", errors="replace") if nodo is not None and nodo.text else None


@dataclass
class Huella:
    """La bolsa de subárboles de una entrega, y la de cada una de sus funciones."""

    bolsa: Counter = field(default_factory=Counter)
    funciones: Dict[str, Counter] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.bolsa.values())


class Huellero:
    """Calcula huellas comparables entre sí: los números de subárbol valen dentro de un huellero."""

    def __init__(self, tamanio_minimo: int = TAMANIO_MINIMO) -> None:
        self.tamanio_minimo = tamanio_minimo
        self._numeros: Dict[Tuple[Any, ...], int] = {}
        self._tamanios: List[int] = []

    def _numero(self, etiqueta: str, hijos: Tuple[int, ...]) -> int:
        clave = (etiqueta, *hijos)
        numero = self._numeros.get(clave)
        if numero is None:
            numero = self._numeros[clave] = len(self._tamanios)
            self._tamanios.append(1 + sum(self._tamanios[h] for h in hijos))
        return numero

    def _etiqueta(self, nodo: Node, propias: Set[str]) -> str:
        if nodo.type in _CON_OPERADOR:
            operador = nodo.child_by_field_name("operator")
            return f"{nodo.type}:{operador.type if operador is not None else ''}"
        if nodo.type == "call_expression":
            funcion = nodo.child_by_field_name("function")
            if funcion is not None and funcion.type == "identifier" and funcion.text:
                nombre = funcion.text.decode("utf-8", errors="replace")
                if nombre not in propias:
                    return f"llamada:{nombre}"
        return _ETIQUETAS.get(nodo.type, nodo.type)

    def _plegar(self, raiz: Node, propias: Set[str], bolsa: Counter) -> None:
        """Numera el árbol de abajo hacia arriba, sin recursión: una expresión larga es muy profunda."""
        pila: List[Tuple[Node, bool]] = [(raiz, False)]
        numeros: Dict[int, int] = {}
        while pila:
            nodo, listo = pila.pop()
            hijos = [] if nodo.type in _HOJAS else [h for h in nodo.named_children if h.type not in _OMITIDOS]
            if not listo:
                pila.append((nodo, True))
                pila.extend((h, False) for h in reversed(hijos))
                continue
            if nodo.type in _HOJAS:
                numeros[nodo.id] = self._numero(_HOJAS[nodo.type], ())
            elif nodo.type in _TRANSPARENTES and len(hijos) == 1:
                numeros[nodo.id] = numeros[hijos[0].id]
            else:
                numero = self._numero(self._etiqueta(nodo, propias), tuple(numeros[h.id] for h in hijos))
                numeros[nodo.id] = numero
                if self._tamanios[numero] >= self.tamanio_minimo:
                    bolsa[numero] += 1

    def huella(self, codigos: Iterable[str]) -> Huella:
        """La huella de una entrega: sus archivos cuentan como un solo programa."""
        arboles = [_analizador().parse(c.encode("utf-8", errors="replace")) for c in codigos]
        definiciones = [n for a in arboles for n in a.root_node.named_children]
        propias = {nombre for a in arboles for nombre in _nombres_propios(a.root_node)}
        huella = Huella()
        for nodo in definiciones:
            if nodo.type in _OMITIDOS or _es_prototipo(nodo):
                continue
            bolsa: Counter = Counter()
            self._plegar(nodo, propias, bolsa)
            huella.bolsa.update(bolsa)
            if nodo.type == "function_definition":
                nombre = _nombre_de_funcion(nodo) or "?"
                huella.funciones.setdefault(nombre, Counter()).update(bolsa)
        return huella


def dice(a: Counter, b: Counter) -> float:
    """Coeficiente de Dice de dos bolsas, en porcentaje."""
    total = sum(a.values()) + sum(b.values())
    return round(200.0 * sum((a & b).values()) / total, 1) if total else 0.0


def contencion(a: Counter, b: Counter) -> float:
    """Qué parte de la bolsa más chica está en la otra: ve una copia con código agregado."""
    menor = min(sum(a.values()), sum(b.values()))
    return round(100.0 * sum((a & b).values()) / menor, 1) if menor else 0.0


def funciones_parecidas(a: Huella, b: Huella, minimo: float = 70.0) -> List[Dict[str, Any]]:
    """Qué función de una entrega se corresponde con cuál de la otra (sólo nombres y porcentajes)."""
    candidatos = sorted(
        ((dice(ba, bb), fa, fb) for fa, ba in a.funciones.items() for fb, bb in b.funciones.items()),
        key=lambda c: (-c[0], c[1], c[2]),
    )
    usadas_a: Set[str] = set()
    usadas_b: Set[str] = set()
    pares: List[Dict[str, Any]] = []
    for valor, fa, fb in candidatos:
        if valor >= minimo and fa not in usadas_a and fb not in usadas_b:
            usadas_a.add(fa)
            usadas_b.add(fb)
            pares.append({"a": fa, "b": fb, "similitud_pct": valor})
    return pares


def _leer(archivos: Iterable[Path]) -> List[str]:
    return [p.read_text(encoding="utf-8", errors="replace") for p in archivos]


def fuentes_de_plantilla(plantilla: Path) -> List[Path]:
    return sorted(plantilla.rglob("*.c")) if plantilla.is_dir() else [plantilla]


def _descontar_comunes(huellas: Mapping[str, Huella], comunes: float) -> int:
    """Quita de cada huella los subárboles de al menos `comunes` de las entregas; cuántos fueron."""
    if not comunes or len(huellas) < ENTREGAS_MINIMAS_PARA_COMUNES:
        return 0
    presencia = Counter(n for h in huellas.values() for n in h.bolsa)
    quitar = {n for n, veces in presencia.items() if veces >= comunes * len(huellas)}
    for huella in huellas.values():
        huella.bolsa = Counter({n: c for n, c in huella.bolsa.items() if n not in quitar})
        huella.funciones = {f: resto for f, b in huella.funciones.items()
                            if (resto := Counter({n: c for n, c in b.items() if n not in quitar}))}
    return len(quitar)


def comparar_lote(entregas: Mapping[str, Iterable[Path]], umbral: float = 90.0,
                  plantilla: Optional[Path] = None, comunes: float = COMUNES) -> Dict[str, Any]:
    """Todas contra todas: la matriz completa, los pares sobre `umbral` y sus grupos.

    `plantilla` es el código de la cátedra: sus subárboles se descuentan de cada entrega, aunque
    la entrega haya renombrado lo que recibió. `comunes` es la fracción de entregas a partir de la
    cual un subárbol se descuenta por común (0 no descuenta). El resultado tiene nombres y
    porcentajes, no código.
    """
    huellero = Huellero()
    base = huellero.huella(_leer(fuentes_de_plantilla(plantilla))) if plantilla is not None else Huella()
    huellas: Dict[str, Huella] = {}
    sin_codigo: List[str] = []
    for nombre, archivos in sorted(entregas.items()):
        huella = huellero.huella(_leer(archivos))
        huella.bolsa -= base.bolsa
        huella.funciones = {f: resto for f, b in huella.funciones.items() if (resto := b - base.bolsa)}
        if huella.total:
            huellas[nombre] = huella
        else:
            sin_codigo.append(nombre)

    descontados = _descontar_comunes(huellas, comunes)
    for nombre in [n for n, h in huellas.items() if not h.total]:
        del huellas[nombre]
        sin_codigo.append(nombre)
    sin_codigo.sort()

    nombres = sorted(huellas)
    matriz: Dict[str, Dict[str, float]] = {n: {n: 100.0} for n in nombres}
    pares: List[Dict[str, Any]] = []
    for a, b in combinations(nombres, 2):
        valor = dice(huellas[a].bolsa, huellas[b].bolsa)
        matriz[a][b] = matriz[b][a] = valor
        if valor >= umbral:
            pares.append({"a": a, "b": b, "similitud_pct": valor,
                          "contencion_pct": contencion(huellas[a].bolsa, huellas[b].bolsa),
                          "funciones": funciones_parecidas(huellas[a], huellas[b])})
    pares.sort(key=lambda p: (-p["similitud_pct"], p["a"], p["b"]))
    return {
        "motor": MOTOR,
        "umbral_pct": umbral,
        "entregas": len(entregas),
        "sin_codigo": sin_codigo,
        "subarboles_comunes": descontados,
        "matriz": matriz,
        "pares": pares,
        "grupos": _grupos(pares, matriz),
    }


def _grupos(pares: List[Dict[str, Any]], matriz: Mapping[str, Mapping[str, float]]) -> List[Dict[str, Any]]:
    """Las componentes conexas de los pares sobre el umbral."""
    padre: Dict[str, str] = {}

    def raiz(n: str) -> str:
        padre.setdefault(n, n)
        while padre[n] != n:
            padre[n] = padre[padre[n]]
            n = padre[n]
        return n

    for par in pares:
        padre[raiz(par["a"])] = raiz(par["b"])
    miembros: Dict[str, List[str]] = {}
    for n in list(padre):
        miembros.setdefault(raiz(n), []).append(n)
    grupos: List[Dict[str, Any]] = []
    for nombres in miembros.values():
        nombres.sort()
        valores = [matriz[a][b] for a, b in combinations(nombres, 2)]
        grupos.append({"entregas": nombres, "similitud_min": min(valores), "similitud_max": max(valores),
                       "matriz": {a: {b: matriz[a][b] for b in nombres} for a in nombres}})
    grupos.sort(key=lambda g: (-len(g["entregas"]), -g["similitud_max"], g["entregas"]))
    return grupos


def entregas_de_directorio(raiz: Path) -> Dict[str, List[Path]]:
    """Una entrega por subcarpeta (con sus `.c`, en cualquier nivel) o por `.c` suelto en `raiz`."""
    entregas: Dict[str, List[Path]] = {}
    for hijo in sorted(raiz.iterdir()):
        if hijo.name.startswith((".", "_")):
            continue
        if hijo.is_dir():
            fuentes = sorted(p for p in hijo.rglob("*.c")
                             if not any(parte.startswith(".") for parte in p.relative_to(hijo).parts))
            if fuentes:
                entregas[hijo.name] = fuentes
        elif hijo.suffix == ".c":
            entregas[hijo.stem] = [hijo]
    return entregas


def matriz_csv(matriz: Mapping[str, Mapping[str, float]]) -> str:
    """La matriz completa como CSV, con una fila y una columna por entrega."""
    import csv
    import io

    nombres = sorted(matriz)
    salida = io.StringIO()
    escritor = csv.writer(salida, lineterminator="\n")
    escritor.writerow(["entrega", *nombres])
    for a in nombres:
        escritor.writerow([a, *(matriz[a].get(b, "") for b in nombres)])
    return salida.getvalue()
