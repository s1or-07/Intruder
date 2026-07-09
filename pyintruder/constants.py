"""Constantes compartidas por el nucleo y la interfaz."""

# Caracter usado para delimitar posiciones de payload (§).
MARKER = "\u00a7"

# Tope de caracteres del cuerpo de respuesta que se guardan para el visor,
# para evitar consumir memoria con respuestas enormes.
MAX_VIEW_BODY = 200_000

# Fuente monoespaciada usada en editores y visores.
MONO = ("Courier New", 10)

# Paleta de colores para el coloreado de sintaxis y la interfaz.
COLORS = {
    "method": "#0b5fa5",
    "version": "#8a8a8a",
    "header_name": "#7b1fa2",
    "header_value": "#1b7a3d",
    "marker_bg": "#ffe08a",
    "marker_fg": "#7a4a00",
    "st2": "#1b7a3d",   # 2xx
    "st3": "#0b5fa5",   # 3xx
    "st4": "#b35a00",   # 4xx
    "st5": "#b00020",   # 5xx
    "reason": "#555555",
    "banner_bg": "#7a1f1f",
    "hit_bg": "#fff3cd",
    "viewer_bg": "#fbfbfb",
}
