"""Módulo de análisis profundo de AST, control de flujo y distancia de edición en WEYL."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from rich.tree import Tree

from weyl.core.alpha_equiv import normalizar_alpha_equivalencia
from weyl.core.differ import _extraer_mapa_funciones


def calcular_distancia_edicion(cuerpo_a: str, cuerpo_b: str) -> float:
    """Calcula una distancia cuantitativa normalizada (0.0 a 100.0) entre dos cuerpos de función."""
    norm_a = normalizar_alpha_equivalencia(cuerpo_a)
    norm_b = normalizar_alpha_equivalencia(cuerpo_b)

    tokens_a = norm_a.split()
    tokens_b = norm_b.split()

    if not tokens_a and not tokens_b:
        return 0.0
    if not tokens_a or not tokens_b:
        return 100.0

    # Distancia de Levenshtein a nivel de tokens
    len_a = len(tokens_a)
    len_b = len(tokens_b)
    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]

    for i in range(len_a + 1):
        dp[i][0] = i
    for j in range(len_b + 1):
        dp[0][j] = j

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            cost = 0 if tokens_a[i - 1] == tokens_b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # eliminación
                dp[i][j - 1] + 1,        # inserción
                dp[i - 1][j - 1] + cost  # sustitución
            )

    dist = dp[len_a][len_b]
    max_len = max(len_a, len_b)
    return round((dist / max_len) * 100.0, 2)


def detectar_recursion_con_acumulador(cuerpo_a: str, cuerpo_b: str, fn_nombre: str) -> Dict[str, Any]:
    """Detecta si se transformó recursión simple a recursión de cola con acumulador (tail-recursion)."""
    llamadas_a = len(re.findall(rf"\b{fn_nombre}\s*\(", cuerpo_a))
    llamadas_b = len(re.findall(rf"\b{fn_nombre}\s*\(", cuerpo_b))

    es_recursiva_a = llamadas_a > 0
    es_recursiva_b = llamadas_b > 0

    acumulador_detectado = False
    if es_recursiva_a or es_recursiva_b:
        # Detectar patrón de retorno directo de la llamada recursiva (tail call)
        patron_tail = re.compile(rf"return\s+{fn_nombre}\s*\([^)]*\)\s*;", re.MULTILINE)
        tail_a = bool(patron_tail.search(cuerpo_a))
        tail_b = bool(patron_tail.search(cuerpo_b))

        # O presencia de variables intermedias acumuladoras
        vars_acc = re.findall(r"\b(acc|acum|acumulador|total|res|subtotal)\b", cuerpo_b, re.IGNORECASE)
        acumulador_detectado = (not tail_a and tail_b) or (len(vars_acc) > 0 and es_recursiva_b)

    return {
        "es_recursiva_estudiante": es_recursiva_a,
        "es_recursiva_modelo": es_recursiva_b,
        "transformacion_acumulador": acumulador_detectado,
        "detalle": "Optimización a recursión de cola con acumulador detectada" if acumulador_detectado else "Sin cambio de tipo de recursión",
    }


def analizar_estilo_control_flujo(codigo: str) -> Dict[str, Any]:
    """Clasifica el estilo de control de flujo: Early Return (Guard Clauses) vs Bloques Anidados."""
    # Contar early returns
    returns_tempranos = len(re.findall(r"if\s*\([^)]*\)\s*return\b", codigo)) + len(
        re.findall(r"if\s*\([^)]*\)\s*\{\s*return\b[^}]*\}", codigo)
    )

    # Medir nivel máximo de anidamiento de llaves
    nivel_max = 0
    nivel_act = 0
    for ch in codigo:
        if ch == '{':
            nivel_act += 1
            if nivel_act > nivel_max:
                nivel_max = nivel_act
        elif ch == '}':
            if nivel_act > 0:
                nivel_act -= 1

    if returns_tempranos >= 2 and nivel_max <= 3:
        estilo = "Guard Clauses (Early Exit)"
    elif nivel_max >= 4:
        estilo = "Bloques Anidados Profundos (Arrow Anti-pattern)"
    else:
        estilo = "Estructurado Estándar"

    return {
        "estilo_predominante": estilo,
        "early_returns_count": returns_tempranos,
        "anidamiento_maximo": nivel_max,
    }


def mapear_llamadas_libc_vs_propias(codigo: str) -> Dict[str, List[str]]:
    """Identifica llamadas a funciones de libc conocidas vs implementaciones artesanales."""
    libc_conocidas = {
        "qsort", "bsearch", "strlen", "strcpy", "strncpy", "strcat", "strncat",
        "strcmp", "strncmp", "strchr", "strstr", "memcpy", "memmove", "memset",
        "memcmp", "malloc", "calloc", "realloc", "free", "printf", "scanf",
        "sprintf", "snprintf", "sscanf", "fopen", "fclose", "fread", "fwrite",
        "fgets", "fputs", "atoi", "strtol", "strtod", "abs", "rand", "srand"
    }

    tokens = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", codigo)
    usadas_libc = sorted(list(set(tok for tok in tokens if tok in libc_conocidas)))

    # Funciones definidas en el propio código
    def_fns = set(re.findall(r"^\s*(?:[a-zA-Z0-9_*]+\s+)+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{", codigo, re.MULTILINE))
    usadas_propias = sorted(list(set(tok for tok in tokens if tok in def_fns)))

    return {
        "libc": usadas_libc,
        "propias": usadas_propias,
    }


def auditar_estructuras_intermedias(codigo: str) -> Dict[str, Any]:
    """Identifica si el algoritmo utiliza memoria dinámica/búfers auxiliares o resuelve in-place."""
    usa_malloc = bool(re.search(r"\b(malloc|calloc|realloc)\s*\(", codigo))
    usa_buffer_local = bool(re.search(r"\b(?:int|char|long|float|double)\s+[a-zA-Z0-9_]+\s*\[[^\]]+\]", codigo))

    if usa_malloc:
        modo = "Memoria Dinámica Auxiliar (Heap Allocation)"
    elif usa_buffer_local:
        modo = "Arreglo Auxiliar en Pila (Stack Buffer)"
    else:
        modo = "Algoritmo In-Place (Sin Memoria Intermedia)"

    return {
        "modo_memoria": modo,
        "usa_heap": usa_malloc,
        "usa_stack_buffer": usa_buffer_local,
    }


def generar_arbol_ast_diff(archivo_estudiante: Path, archivo_modelo: Path) -> Tree:
    """Genera un árbol Rich navegable visualizando las discrepancias sintácticas y de diseño."""
    txt_est = archivo_estudiante.read_text(encoding="utf-8", errors="replace") if archivo_estudiante.is_file() else ""
    txt_mod = archivo_modelo.read_text(encoding="utf-8", errors="replace") if archivo_modelo.is_file() else ""

    fns_est = _extraer_mapa_funciones(txt_est)
    fns_mod = _extraer_mapa_funciones(txt_mod)

    raiz = Tree(f"🌳 [bold cyan]AST Diff:[/bold cyan] {archivo_estudiante.name} ➔ {archivo_modelo.name}")

    todos_nombres = sorted(set(fns_est.keys()) | set(fns_mod.keys()))

    for fn in todos_nombres:
        c_est = fns_est.get(fn)
        c_mod = fns_mod.get(fn)

        if c_est and not c_mod:
            fn_node = raiz.add(f"[bold blue]+ {fn}()[/bold blue] [dim](Función auxiliar agregada)[/dim]")
            analisis = auditar_estructuras_intermedias(c_est)
            fn_node.add(f"📦 Memoria: {analisis['modo_memoria']}")
        elif not c_est and c_mod:
            raiz.add(f"[bold red]- {fn}()[/bold red] [dim](Función ausente en la entrega)[/dim]")
        else:
            dist = calcular_distancia_edicion(c_est, c_mod)
            color = "green" if dist == 0 else "yellow" if dist < 30 else "magenta"
            fn_node = raiz.add(f"[{color}]~ {fn}()[/{color}] (Distancia AST: {dist:.1f}%)")

            # Analizar control de flujo
            cf_est = analizar_estilo_control_flujo(c_est)
            cf_mod = analizar_estilo_control_flujo(c_mod)
            if cf_est["estilo_predominante"] != cf_mod["estilo_predominante"]:
                fn_node.add(f"🔀 Estilo: [yellow]{cf_est['estilo_predominante']}[/yellow] (Modelo: {cf_mod['estilo_predominante']})")

            # Analizar llamadas a libc
            libc_info = mapear_llamadas_libc_vs_propias(c_est)
            if libc_info["libc"]:
                fn_node.add(f"📚 Primitivas libc: {', '.join(libc_info['libc'])}")

    return raiz
