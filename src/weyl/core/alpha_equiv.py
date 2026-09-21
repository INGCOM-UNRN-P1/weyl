"""Módulo de equivalencia semántica pura (Alpha-Equivalence) y normalización lógica en WEYL."""

from __future__ import annotations

import re
from typing import Dict, Tuple


def normalizar_alpha_equivalencia(codigo: str) -> str:
    """Normaliza nombres de variables locales y parámetros a identificadores canónicos (_v0, _v1, ...).
    
    Permite verificar Alpha-Equivalence: dos códigos con idéntica estructura lógica pero
    diferentes nombres de variables se identifican como equivalentes.
    """
    # Excluir palabras reservadas de C y tipos estándar
    palabras_clave = {
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "int", "long", "register", "return", "short", "signed", "sizeof", "static",
        "struct", "switch", "typedef", "union", "unsigned", "void", "volatile",
        "while", "size_t", "ssize_t", "int8_t", "int16_t", "int32_t", "int64_t",
        "uint8_t", "uint16_t", "uint32_t", "uint64_t", "bool", "true", "false",
        "NULL", "printf", "scanf", "malloc", "free", "calloc", "realloc", "memcpy",
        "memset", "strlen", "strcpy", "strncpy", "strcmp", "strncmp"
    }

    # Tokenizar identificadores
    tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", codigo)
    mapeo: Dict[str, str] = {}
    contador = 0

    for tok in tokens:
        if tok not in palabras_clave and not tok.startswith("__"):
            if tok not in mapeo:
                mapeo[tok] = f"_v{contador}"
                contador += 1

    def reemplazar_token(match: re.Match) -> str:
        t = match.group(0)
        return mapeo.get(t, t)

    res = re.sub(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", reemplazar_token, codigo)
    # Normalizar espacios en blanco
    res = re.sub(r"\s+", " ", res).strip()
    return res


# Negación de cada operador relacional.
_NEGACION_RELACIONAL = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}
_RELACIONAL = re.compile(r"^(.+?)(==|!=|<=|>=|<|>)(.+)$")


def _son_condiciones_negadas(cond_a: str, cond_b: str) -> bool:
    """True si una condición es exactamente la negación lógica de la otra.

    Las variables se normalizan por posición, así que `x>5` y `y<=5` cuentan
    como negadas (mismos operandos, operador opuesto), pero `x>5` y `y<=100`
    no: los operandos difieren.
    """
    a = cond_a.replace(" ", "")
    b = cond_b.replace(" ", "")
    na, nb = normalizar_alpha_equivalencia(a), normalizar_alpha_equivalencia(b)

    for x, y in ((na, nb), (nb, na)):
        if x == normalizar_alpha_equivalencia(f"!({y})") or x == normalizar_alpha_equivalencia(f"!{y}"):
            return True

    ma, mb = _RELACIONAL.match(na), _RELACIONAL.match(nb)
    if ma and mb:
        return (
            ma.group(1) == mb.group(1)
            and ma.group(3) == mb.group(3)
            and _NEGACION_RELACIONAL[ma.group(2)] == mb.group(2)
        )
    return False


def detectar_inversion_if_else(cuerpo_a: str, cuerpo_b: str) -> bool:
    """Detecta si dos bloques condicionales representan lógica equivalente con condición invertida.
    
    Ejemplo:
      if (cond) { ramaA } else { ramaB }  vs  if (!cond) { ramaB } else { ramaA }
    """
    re_if_else = re.compile(
        r"if\s*\((.*?)\)\s*\{([^}]*)\}\s*else\s*\{([^}]*)\}",
        re.DOTALL
    )
    m_a = re_if_else.search(cuerpo_a)
    m_b = re_if_else.search(cuerpo_b)

    if not m_a or not m_b:
        return False

    cond_a, then_a, else_a = m_a.group(1).strip(), m_a.group(2).strip(), m_a.group(3).strip()
    cond_b, then_b, else_b = m_b.group(1).strip(), m_b.group(2).strip(), m_b.group(3).strip()

    # Normalizar ramas
    norm_then_a = normalizar_alpha_equivalencia(then_a)
    norm_else_a = normalizar_alpha_equivalencia(else_a)
    norm_then_b = normalizar_alpha_equivalencia(then_b)
    norm_else_b = normalizar_alpha_equivalencia(else_b)

    # Caso 1: ramas cruzadas
    ramas_cruzadas = (norm_then_a == norm_else_b) and (norm_else_a == norm_then_b)
    if not ramas_cruzadas:
        return False

    # Con las ramas cruzadas, el resultado solo es equivalente si las
    # condiciones son la NEGACIÓN una de la otra. El `return True` final que
    # había antes convertía toda comparación de ramas cruzadas en "equivalente"
    # (con `if(x>5){1}else{2}` vs `if(y<100){2}else{1}` inclusive), volviendo
    # decorativas las verificaciones de negación anteriores.
    return _son_condiciones_negadas(cond_a, cond_b)


def _cierre(texto: str, abre: int, par: str) -> int:
    """Índice del delimitador que cierra el que está en `abre` (-1 si no cierra)."""
    cierra = {"(": ")", "{": "}"}[par]
    nivel = 0
    for k in range(abre, len(texto)):
        if texto[k] == par:
            nivel += 1
        elif texto[k] == cierra:
            nivel -= 1
            if nivel == 0:
                return k
    return -1


def _partes_del_encabezado(encabezado: str):
    """Separa `init; cond; paso` respetando los paréntesis anidados."""
    partes, nivel, actual = [], 0, ""
    for c in encabezado:
        if c == "(":
            nivel += 1
        elif c == ")":
            nivel -= 1
        if c == ";" and nivel == 0:
            partes.append(actual.strip())
            actual = ""
        else:
            actual += c
    partes.append(actual.strip())
    return partes if len(partes) == 3 else None


def desazucarar_for_a_while(codigo: str) -> str:
    """Reescribe cada `for (init; cond; paso) { cuerpo }` como `init; while (cond) { cuerpo paso; }`.

    Solo trata los `for` con llaves y con el encabezado bien formado; los demás
    quedan intactos, de modo que nunca se afirma una equivalencia que no se
    pudo construir.
    """
    salida = codigo
    inicio_busqueda = 0
    while True:
        m = re.compile(r"\bfor\s*\(").search(salida, inicio_busqueda)
        if not m:
            return salida
        abre = m.end() - 1
        cierra = _cierre(salida, abre, "(")
        partes = _partes_del_encabezado(salida[abre + 1:cierra]) if cierra > 0 else None
        resto = salida[cierra + 1:].lstrip() if cierra > 0 else ""
        if not partes or not resto.startswith("{"):
            inicio_busqueda = m.end()
            continue
        abre_cuerpo = len(salida) - len(resto)
        cierra_cuerpo = _cierre(salida, abre_cuerpo, "{")
        if cierra_cuerpo < 0:
            inicio_busqueda = m.end()
            continue
        init, cond, paso = partes
        cuerpo = salida[abre_cuerpo + 1:cierra_cuerpo].strip()
        reemplazo = f"{init + '; ' if init else ''}while ({cond or '1'}) {{ {cuerpo} {paso + ';' if paso else ''} }}"
        salida = salida[:m.start()] + reemplazo + salida[cierra_cuerpo + 1:]
        inicio_busqueda = m.start()


def detectar_equivalencia_for_while(cuerpo_a: str, cuerpo_b: str) -> bool:
    """True si un `for` y un `while` son el mismo bucle escrito de dos maneras.

    Antes bastaba con que ambos usaran los mismos operadores (`<`, `++`...),
    de modo que `for (i<10; i++)` y un `while (j<20) { k++ }` cualquiera
    contaban como equivalentes. Ahora el `for` se reescribe como `while`
    (init antes, paso al final del cuerpo) y se exige que el texto resultante
    sea alfa-equivalente al del otro código.
    """
    hay_for_a, hay_for_b = re.search(r"\bfor\s*\(", cuerpo_a), re.search(r"\bfor\s*\(", cuerpo_b)
    hay_while_a, hay_while_b = re.search(r"\bwhile\s*\(", cuerpo_a), re.search(r"\bwhile\s*\(", cuerpo_b)
    if not ((hay_for_a and hay_while_b) or (hay_while_a and hay_for_b)):
        return False
    a, b = desazucarar_for_a_while(cuerpo_a), desazucarar_for_a_while(cuerpo_b)
    if a == cuerpo_a and b == cuerpo_b:
        return False
    return normalizar_alpha_equivalencia(a) == normalizar_alpha_equivalencia(b)
