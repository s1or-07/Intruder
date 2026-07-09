# PyIntruder

Fuzzer de peticiones HTTP con interfaz gráfica, inspirado en el módulo **Intruder** de Burp Suite. Toma una petición HTTP base, inserta payloads en posiciones marcadas con `§`, envía cada variante y recopila las respuestas para su análisis.

> ⚠️ **Uso autorizado únicamente.** Empléalo solo sobre sistemas para los que tengas autorización (laboratorios propios, certificaciones/exámenes, bug bounty dentro de alcance). No me hago responsable del mal uso.

## Requisitos

- **Python 3.8+** con **Tkinter** (incluido en las instalaciones de escritorio estándar).
- Sin dependencias externas: solo librería estándar.

Si Tkinter no estuviera disponible: `sudo apt install python3-tk` (Debian/Ubuntu) · `sudo dnf install python3-tkinter` (Fedora). En Windows/macOS con el instalador de python.org ya viene incluido.

## Ejecución

Desde la raíz del proyecto, cualquiera de estas formas:

```bash
python3 run.py
# o
python3 -m pyintruder
```

Instalación opcional como paquete (crea el comando `pyintruder`):

```bash
pip install -e .
pyintruder
```

## Estructura del proyecto

```
pyintruder/                  Proyecto
├── run.py                   Lanzador rápido
├── pyproject.toml           Metadatos / instalación opcional
├── README.md
└── pyintruder/              Paquete
    ├── __init__.py
    ├── __main__.py          Permite  python -m pyintruder
    ├── constants.py         Constantes y paleta de colores compartidas
    ├── core/                Lógica pura (sin interfaz, testeable aislada)
    │   ├── __init__.py
    │   ├── template.py      RequestTemplate: posiciones § y construcción de variantes
    │   ├── attacks.py       Tipos de ataque: generación y conteo
    │   ├── http_client.py   Parseo y envío de peticiones HTTP/HTTPS
    │   └── engine.py        AttackEngine: motor concurrente
    └── gui/                 Interfaz (Tkinter), dividida por componentes
        ├── __init__.py
        ├── app.py           Ventana principal: ensambla paneles y ciclo del ataque
        ├── highlighting.py  Coloreado de sintaxis HTTP (editor y visores)
        ├── request_panel.py Panel izquierdo: editor de la petición y objetivo
        ├── sidebar.py       Menú lateral: ataque, payloads, opciones y grep
        └── results_panel.py Pestaña de resultados: tabla + visores req/resp
```

La separación **core / gui** permite probar y reutilizar toda la lógica sin depender de la interfaz; de hecho el núcleo puede usarse desde un script:

```python
from pyintruder.core import RequestTemplate, AttackEngine, count_requests
```

## Interfaz

**Pestaña 1 - Petición y ataque.** A la izquierda, el editor de la petición con coloreado de sintaxis HTTP y posiciones `§` resaltadas; arriba, Host / Puerto / HTTPS (botón *Auto*). A la derecha, un menú lateral con el tipo de ataque, la lista de payloads, las opciones (concurrencia, retardo, timeout, `Content-Length`) y *Grep – Match*.

**Pestaña 2 - Resultados.** Tabla ordenable por cualquier columna (las filas con coincidencia grep se resaltan) y, debajo, dos visores que muestran el *Request enviado* y el *Response recibido* completos al seleccionar una fila, con el código de estado coloreado por clase (2xx verde, 3xx azul, 4xx naranja, 5xx rojo).

## Tipos de ataque

| Tipo | Conjuntos | Inserción | Nº de peticiones |
|---|---|---|---|
| Sniper | 1 | una posición por turno | posiciones × payloads |
| Battering ram | 1 | mismo payload en todas | payloads |
| Pitchfork | varios | paralelo simultáneo | conjunto más corto |
| Cluster bomb | varios | todas las combinaciones | producto de los conjuntos |

## Notas

Herramienta de propósito general equivalente conceptualmente a `ffuf`/`wfuzz`, pensada para aprender y para pruebas autorizadas. No incluye evasión de WAF, bypass de CAPTCHA, rotación de proxies ni listas de credenciales preempaquetadas. Para no saturar el objetivo, mantén una concurrencia baja y usa el retardo entre peticiones.
