# ⚖️ WEYL — Diffing Semántico y Comparación AST en C

WEYL compara semánticamente dos archivos de código fuente C función por función, abstrayendo diferencias de espaciado para identificar qué funciones fueron agregadas, eliminadas o modificadas respecto a la solución modelo.

## Uso Rápido

```bash
# 1. Comparar entrega de estudiante contra solución modelo
weyl diff estudiante.c modelo.c

# 2. Salida estructurada JSON
weyl diff estudiante.c modelo.c --json
```
