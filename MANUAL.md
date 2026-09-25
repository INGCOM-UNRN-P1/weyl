# Manual de Uso y Referencia Técnica: weyl

> **WEYL** — Herramienta de diffing semántico y comparación estructural (por bloques y funciones) entre códigos C
> **Versión:** `0.1.0` · **CLI principal:** `weyl` · **Plugin Ripley:** `semantic_diff`

---

## 1. Arquitectura y Propósito Pedagógico

`weyl` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Comparación semántica y diffing estructural de código C por bloques y funciones. La extracción es textual (expresiones regulares y balanceo de llaves sobre el fuente sin comentarios ni literales): **no construye un AST** ni usa Tree-Sitter.
- Identificación de divergencias algorítmicas entre entregas de estudiantes y soluciones modelo canónicas.
- Resistencia a técnicas de ofuscación de código: inmune a renombrado de variables, reordenamiento de funciones y cambios superficiales de formato.
- Detección de copias y similitud semántica profunda entre códigos fuente.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Detección de plagio léxico por huellas de Winnowing (delegado a `dredd`).
- Linter de estilo y formato de código (delegado a `gaff`).
- Ejecución de testcases (delegado a `nostromo`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/weyl
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
weyl doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`weyl check`](#check) | Compara semánticamente ambos códigos función por función. |
| [`weyl diff`](#diff) | Compara semánticamente ambos códigos función por función. |
| [`weyl doctor`](#doctor) | Verifica el estado del entorno de diffing semántico WEYL. |
| [`weyl track`](#track) | Analiza la evolución semántica y mejoras introducidas entre revisiones sucesivas de un estudiante. |
| [`weyl report`](#report) | Genera directamente la sección de reporte Markdown de WEYL para Dredd. |
| [`weyl check-api`](#checkapi) | Verifica que las firmas de funciones respeten los contratos y parámetros de la consigna. |
| [`weyl check-complexity`](#checkcomplexity) | Detecta transformaciones algorítmicas, reducciones de anidación o cambio recursión/iteración. |
| [`weyl detect-orphans`](#detectorphans) | Detecta funciones auxiliares huérfanas o código muerto agregado en la entrega. |
| [`weyl export-html`](#exporthtml) | Genera un reporte interactivo en formato HTML con diferencias semánticas. |
| [`weyl ast-diff`](#astdiff) | Visualiza en formato jerárquico Rich el árbol de funciones y bloques (no es un AST del compilador). |
| [`weyl matrix`](#matrix) | Genera la matriz cruzada de similitud función por función bajo Alpha-Equivalence. |
| [`weyl diff-project`](#diffproject) | Realiza diffing semántico modular entre proyectos con múltiples archivos .c. |
| [`weyl audit-memory`](#auditmemory) | Audita cambios en llamadas a malloc, calloc, realloc y free entre dos revisiones. |
| [`weyl check-plagiarism`](#checkplagiarism) | Detecta plagio semántico resistente a renombramiento de variables y reordenamiento. |

### `weyl check`

Compara semánticamente ambos códigos función por función.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--side-by-side`, `-s` | `bool` | `False` | Visualizar comparación lado a lado en dos columnas. |
| `--alpha`, `-a` | `bool` | `False` | Activar normalización de identificadores (Alpha-Equivalence). |
| `--json` | `bool` | `False` | Salida en formato JSON. |
| `--md`, `--output-md`, `-o` | `Optional[Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
weyl check <estudiante> <modelo>
```

### `weyl diff`

Compara semánticamente ambos códigos función por función.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--side-by-side`, `-s` | `bool` | `False` | Visualizar comparación lado a lado en dos columnas. |
| `--alpha`, `-a` | `bool` | `False` | Activar normalización de identificadores (Alpha-Equivalence). |
| `--json` | `bool` | `False` | Salida en formato JSON. |
| `--md`, `--output-md`, `-o` | `Optional[Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
weyl diff <estudiante> <modelo>
```

### `weyl doctor`

Verifica el estado del entorno de diffing semántico WEYL.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl doctor
```

### `weyl track`

Analiza la evolución semántica y mejoras introducidas entre revisiones sucesivas de un estudiante.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `dir_r1` | `Path` | Directorio o archivo de la revisión inicial (r1). |
| `dir_r2` | `Path` | Directorio o archivo de la reentrega (r2). |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl track <dir_r1> <dir_r2>
```

### `weyl report`

Genera directamente la sección de reporte Markdown de WEYL para Dredd.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[Path]` | `None` | Ruta de destino del archivo Markdown. |

#### Ejemplo de Invocación
```bash
weyl report <estudiante> <modelo>
```

### `weyl check-api`

Verifica que las firmas de funciones respeten los contratos y parámetros de la consigna.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl check-api <estudiante> <modelo>
```

### `weyl check-complexity`

Detecta transformaciones algorítmicas, reducciones de anidación o cambio recursión/iteración.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl check-complexity <estudiante> <modelo>
```

### `weyl detect-orphans`

Detecta funciones auxiliares huérfanas o código muerto agregado en la entrega.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante a auditar. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl detect-orphans <estudiante>
```

### `weyl export-html`

Genera un reporte interactivo en formato HTML con diferencias semánticas.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Path` | `weyl_report.html` | Ruta de destino del reporte HTML interactivo. |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl export-html <estudiante> <modelo>
```

### `weyl ast-diff`

Visualiza en formato jerárquico Rich el árbol de funciones y bloques (no es un AST del compilador).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl ast-diff <estudiante> <modelo>
```

### `weyl matrix`

Genera la matriz cruzada de similitud función por función bajo Alpha-Equivalence.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `estudiante` | `Path` | Código C del estudiante. |
| `modelo` | `Path` | Código C de la solución modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl matrix <estudiante> <modelo>
```

### `weyl diff-project`

Realiza diffing semántico modular entre proyectos con múltiples archivos .c.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `dir_estudiante` | `Path` | Directorio del proyecto del estudiante. |
| `dir_modelo` | `Path` | Directorio del proyecto modelo. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir resultado en JSON. |

#### Ejemplo de Invocación
```bash
weyl diff-project <dir_estudiante> <dir_modelo>
```

### `weyl audit-memory`

Audita cambios en llamadas a malloc, calloc, realloc y free entre dos revisiones.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `revision1` | `Path` | Directorio o archivo de la revisión 1. |
| `revision2` | `Path` | Directorio o archivo de la revisión 2. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir resultado en JSON. |

#### Ejemplo de Invocación
```bash
weyl audit-memory <revision1> <revision2>
```

### `weyl check-plagiarism`

Detecta plagio semántico resistente a renombramiento de variables y reordenamiento.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `entrega1` | `Path` | Código C de la primera entrega. |
| `entrega2` | `Path` | Código C de la segunda entrega. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--threshold`, `-t` | `float` | `90.0` | Umbral de similitud porcentual para sospecha de copia. |
| `--json` | `bool` | `False` | Emitir el resultado en JSON versionado (schema_version). |

#### Ejemplo de Invocación
```bash
weyl check-plagiarism <entrega1> <entrega2>
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
weyl check --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: weyl, tool=weyl, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`weyl` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
weyl doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.