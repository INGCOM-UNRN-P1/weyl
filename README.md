# ⚖️ WEYL — Diffing Semántico y Comparación AST en C

WEYL compara semánticamente dos archivos de código fuente C función por función, abstrayendo diferencias de espaciado para identificar qué funciones fueron agregadas, eliminadas o modificadas respecto a la solución modelo.

---

## 🎯 Alcance

### Qué cubre
- Comparación semántica y diffing estructural de código C basado en Abstract Syntax Trees (AST).
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
- Ninguno obligatorio (análisis estático con Tree-Sitter AST).

### Integración en el Ecosistema
- CLI `weyl`. Plugin registrado en `ripley.plugins` (`semantic_diff`).

---

## Uso Rápido

```bash
# 1. Comparar entrega de estudiante contra solución modelo
weyl diff estudiante.c modelo.c

# 2. Salida estructurada JSON
weyl diff estudiante.c modelo.c --json
```
