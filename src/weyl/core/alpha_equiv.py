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

    # Verificar si una condición es la negación sintáctica de la otra
    clean_cond_a = cond_a.replace(" ", "")
    clean_cond_b = cond_b.replace(" ", "")

    if clean_cond_a == f"!({clean_cond_b})" or clean_cond_b == f"!({clean_cond_a})":
        return True
    if clean_cond_a == f"!{clean_cond_b}" or clean_cond_b == f"!{clean_cond_a}":
        return True
    if ("==" in clean_cond_a and "!=" in clean_cond_b) or ("!=" in clean_cond_a and "==" in clean_cond_b):
        return True
    if ("<" in clean_cond_a and ">=" in clean_cond_b) or (">=" in clean_cond_a and "<" in clean_cond_b):
        return True
    if (">" in clean_cond_a and "<=" in clean_cond_b) or ("<=" in clean_cond_a and ">" in clean_cond_b):
        return True

    return True


def detectar_equivalencia_for_while(cuerpo_a: str, cuerpo_b: str) -> bool:
    """Detecta si un bucle while y un bucle for resuelven la misma lógica de iteración."""
    tiene_for_a = "for (" in cuerpo_a or "for(" in cuerpo_a
    tiene_while_a = "while (" in cuerpo_a or "while(" in cuerpo_a
    tiene_for_b = "for (" in cuerpo_b or "for(" in cuerpo_b
    tiene_while_b = "while (" in cuerpo_b or "while(" in cuerpo_b

    # Uno debe contener for y el otro while
    if (tiene_for_a and tiene_while_b) or (tiene_while_a and tiene_for_b):
        norm_a = normalizar_alpha_equivalencia(cuerpo_a)
        norm_b = normalizar_alpha_equivalencia(cuerpo_b)
        # Extraer variables y operadores matemáticos principales
        ops_a = sorted(re.findall(r"(\+\+|--|\+=|-=|\*=|/=|<=|>=|<|>|==|!=)", norm_a))
        ops_b = sorted(re.findall(r"(\+\+|--|\+=|-=|\*=|/=|<=|>=|<|>|==|!=)", norm_b))
        return ops_a == ops_b and len(ops_a) > 0
    return False
