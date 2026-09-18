"""Manejo de comentarios y literales de C sin confundirlos entre sí.

El extractor de funciones de WEYL trabaja con expresiones regulares y un
contador de llaves. Ambos fallan si no distinguen el código de los literales de
cadena y de los comentarios:

- `printf("http://ejemplo")` tenía su `//` interpretado como comentario y el
  código se recortaba en `printf("http:`.
- Una llave dentro de un literal (`"}"`) descuadraba el contador y cortaba la
  función en el lugar equivocado.
"""

from __future__ import annotations


def _fin_de_literal(texto: str, inicio: int) -> int:
    """Devuelve el índice posterior al literal de cadena/carácter que empieza en `inicio`."""
    comilla = texto[inicio]
    j, n = inicio + 1, len(texto)
    while j < n:
        if texto[j] == "\\":
            j += 2
            continue
        if texto[j] == comilla:
            return j + 1
        if texto[j] == "\n":
            return j
        j += 1
    return n


def eliminar_comentarios(texto: str) -> str:
    """Elimina los comentarios de línea y de bloque, respetando los literales."""
    salida = []
    i, n = 0, len(texto)
    while i < n:
        par = texto[i:i + 2]
        if par == "//":
            fin = texto.find("\n", i)
            i = n if fin == -1 else fin
        elif par == "/*":
            fin = texto.find("*/", i + 2)
            i = n if fin == -1 else fin + 2
        elif texto[i] in ('"', "'"):
            fin = _fin_de_literal(texto, i)
            salida.append(texto[i:fin])
            i = fin
        else:
            salida.append(texto[i])
            i += 1
    return "".join(salida)


def blanquear_literales(texto: str) -> str:
    """Reemplaza el contenido de cada literal por espacios, conservando longitud y saltos de línea."""
    salida = []
    i, n = 0, len(texto)
    while i < n:
        if texto[i] in ('"', "'"):
            fin = _fin_de_literal(texto, i)
            salida.append(texto[i] + "".join("\n" if c == "\n" else " " for c in texto[i + 1:fin - 1]) + (texto[fin - 1] if fin - 1 > i else ""))
            i = fin
        else:
            salida.append(texto[i])
            i += 1
    return "".join(salida)
