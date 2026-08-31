---
title: "Manual de Referencia: weyl"
subtitle: "Weyl — Diffing Semántico y Comparación Estructural de ASTs contra Soluciones Canónicas"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-weyl)=
# Weyl — Diffing Semántico y Comparación Estructural de ASTs contra Soluciones Canónicas

````{abstract}
**Rol en el ecosistema:** Comparación estructural y semántica de código C entre la entrega del estudiante y la solución de referencia docente, ignorando cambios cosméticos de nombres de variables, espacios y comentarios.
````

---

(manual-weyl-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`weyl`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-weyl-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `weyl`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
weyl doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-weyl-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `weyl`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `weyl diff src/lista.c canon/lista_canon.c` | Compara semánticamente dos implementaciones C a nivel AST. |
| `weyl ast-dump <archivo.c>` | Visualiza el árbol sintáctico abstracto normalizado. |
| `weyl similarity src/ canon/ --threshold 0.80` | Calcula el porcentaje de equivalencia estructural de la solución. |
| `weyl doctor` | Comprueba el motor Tree-Sitter de C. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-weyl-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
// Implementación A (Estudiante)
int suma(int x, int y) {
    int res = x + y;
    return res;
}

// Implementación B (Solución Canónica Docente)
// Weyl detecta que ambas son semánticamente equivalentes a nivel AST
int suma(int a, int b) {
    return a + b;
}
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
weyl diff src/lista.c canon/lista_canon.c
````

### Salida Obtenida en Consola

````{code-block} text
WEYL SEMANTIC DIFF:
┌───────────────────────────┬────────────────────────────────────────────────────────┐
│ Métrica                   │ Resultado                                              │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ Similitud Estructural AST │ 98.4% (Equivalencia Semántica Canónica)                │
│ Funciones Homólogas       │ 4/4 identificadas (lista_crear, insertar, borrar, fin) │
│ Diferencias Detectadas    │ Variable intermedia 'res' omitida en versión canónica  │
└───────────────────────────┴────────────────────────────────────────────────────────┘
[✓] La solución del estudiante cumple con la estructura arquitectónica esperada.
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-weyl-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`weyl`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Comparación Semántica contra Solución Docente
Verificar si el algoritmo implementado coincide estructuralmente con la solución modelo.

**Instrucción de ejecución:**
```bash
weyl diff src/lista.c canon/lista_canon.c
```
````

````{solution} Desafío 1
```bash
weyl diff src/lista.c canon/lista_canon.c
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Inspección del Árbol AST Normalizado
Examinar cómo Weyl abstrae los nombres de variables.

**Instrucción de ejecución:**
```bash
weyl ast-dump src/ordenamiento.c
```
````

````{solution} Desafío 2
```bash
weyl ast-dump src/ordenamiento.c
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Detección de Funciones Faltantes
Comprobar qué funciones requeridas de la API no fueron implementadas.

**Instrucción de ejecución:**
```bash
weyl diff src/tda.c canon/tda.c --check-missing
```
````

````{solution} Desafío 3
```bash
weyl diff src/tda.c canon/tda.c --check-missing
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-weyl-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `weyl` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-weyl:
	@echo "=== Ejecutando verificación con weyl ==="
	weyl check src/ include/

.PHONY: check-weyl
````

Ejecutá `make check-weyl` antes de cada commit para asegurar que tu código conserve el estado de aprobación.
