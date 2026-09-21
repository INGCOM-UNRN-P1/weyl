# ⚖️ WEYL — Diffing Semántico y Comparación Estructural en C

WEYL compara semánticamente dos archivos de código fuente C función por función, abstrayendo diferencias de espaciado para identificar qué funciones fueron agregadas, eliminadas o modificadas respecto a la solución modelo.

---

## 🎯 Alcance

### Qué cubre
- Comparación semántica y diffing estructural de código C por bloques y funciones. La extracción es textual (expresiones regulares y balanceo de llaves sobre el fuente sin comentarios ni literales): **no construye un AST** ni usa Tree-Sitter.
- Identificación de divergencias algorítmicas entre entregas de estudiantes y soluciones modelo canónicas.
- Resistencia a técnicas de ofuscación de código: inmune a renombrado de variables, reordenamiento de funciones y cambios superficiales de formato.
- Detección de copias y similitud semántica profunda entre códigos fuente.

### Qué no cubre (Límites y Delegación)
- Detección de plagio léxico por huellas de Winnowing (delegado a `dredd`).
- Linter de estilo y formato de código (delegado a `gaff`).
- Ejecución de testcases (delegado a `nostromo`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Multiplataforma. Python >= 3.10.

### Dependencias Externas y Binarios
- Ninguno obligatorio (motor estático con análisis estructural por bloques y regex).
- `giger` (opcional): `weyl detect-orphans` le pide el grafo de llamadas por `giger check --json` y, si no está instalado o no responde, usa su detector propio de funciones no invocadas.

### Integración en el Ecosistema
- CLI `weyl`. Plugin registrado en `ripley.plugins` (`semantic_diff`).

---

## Uso Rápido

```bash
# 1. Comparar entrega de estudiante contra solución modelo
weyl diff estudiante.c modelo.c

# 2. Salida estructurada JSON
weyl diff estudiante.c modelo.c --json

# 3. Comparar proyectos completos de múltiples archivos
weyl diff-project dir_alumno/ dir_modelo/

# 4. Auditoría de balance de memoria dinámica (malloc / free)
weyl audit-memory estudiante.c

# 5. Detección de similitud y copia profunda
weyl check-plagiarism entrega1.c entrega2.c

# 6. Diagnóstico del entorno y dependencias
weyl doctor
```
