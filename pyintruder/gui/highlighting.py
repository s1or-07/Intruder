"""Coloreado de sintaxis HTTP para widgets Text de Tkinter.

Funciones independientes de cualquier panel: operan sobre el widget recibido,
de modo que tanto el editor de la peticion como los visores de resultados
comparten exactamente el mismo resaltado.
"""

import re

from ..constants import COLORS, MARKER, MONO

_BOLD = (MONO[0], MONO[1], "bold")


def configure_http_tags(widget):
    """Define los estilos (tags) de coloreado en un widget Text."""
    widget.tag_configure("method", foreground=COLORS["method"], font=_BOLD)
    widget.tag_configure("version", foreground=COLORS["version"])
    widget.tag_configure("header_name", foreground=COLORS["header_name"], font=_BOLD)
    widget.tag_configure("header_value", foreground=COLORS["header_value"])
    widget.tag_configure("marker", background=COLORS["marker_bg"],
                         foreground=COLORS["marker_fg"], font=_BOLD)
    widget.tag_configure("st2", foreground=COLORS["st2"], font=_BOLD)
    widget.tag_configure("st3", foreground=COLORS["st3"], font=_BOLD)
    widget.tag_configure("st4", foreground=COLORS["st4"], font=_BOLD)
    widget.tag_configure("st5", foreground=COLORS["st5"], font=_BOLD)
    widget.tag_configure("reason", foreground=COLORS["reason"])


def _tag(widget, tag, a, b):
    if b > a:
        widget.tag_add(tag, f"1.0+{a}c", f"1.0+{b}c")


def highlight_request(widget):
    """Colorea una peticion HTTP: linea de peticion, cabeceras y marcadores §."""
    s = widget.get("1.0", "end-1c")
    for t in ("method", "version", "header_name", "header_value", "marker"):
        widget.tag_remove(t, "1.0", "end")
    blank = s.find("\n\n")
    head = s if blank == -1 else s[:blank]
    offset = 0
    for i, line in enumerate(head.split("\n")):
        ls = offset
        if i == 0:
            sp = line.find(" ")
            if sp > 0:
                _tag(widget, "method", ls, ls + sp)
            m = re.search(r"HTTP/\d(?:\.\d)?\s*$", line)
            if m:
                _tag(widget, "version", ls + m.start(), ls + len(line))
        else:
            c = line.find(":")
            if c > 0:
                _tag(widget, "header_name", ls, ls + c)
                _tag(widget, "header_value", ls + c + 1, ls + len(line))
        offset += len(line) + 1
    pos = [m.start() for m in re.finditer(re.escape(MARKER), s)]
    for j in range(0, len(pos) - 1, 2):
        _tag(widget, "marker", pos[j], pos[j + 1] + 1)
    widget.tag_raise("marker")


def highlight_response(widget):
    """Colorea una respuesta HTTP: linea de estado (por clase) y cabeceras."""
    s = widget.get("1.0", "end-1c")
    for t in ("version", "header_name", "header_value",
              "st2", "st3", "st4", "st5", "reason"):
        widget.tag_remove(t, "1.0", "end")
    blank = s.find("\n\n")
    head = s if blank == -1 else s[:blank]
    offset = 0
    for i, line in enumerate(head.split("\n")):
        ls = offset
        if i == 0:
            m = re.match(r"(HTTP/\d(?:\.\d)?)\s+(\d{3})(.*)$", line)
            if m:
                _tag(widget, "version", ls + m.start(1), ls + m.end(1))
                tag = {"2": "st2", "3": "st3",
                       "4": "st4", "5": "st5"}.get(m.group(2)[0], "reason")
                _tag(widget, tag, ls + m.start(2), ls + m.end(2))
                _tag(widget, "reason", ls + m.start(3), ls + len(line))
        else:
            c = line.find(":")
            if c > 0:
                _tag(widget, "header_name", ls, ls + c)
                _tag(widget, "header_value", ls + c + 1, ls + len(line))
        offset += len(line) + 1


def set_viewer(widget, text, kind):
    """Carga texto en un visor de solo lectura y lo colorea.

    kind: 'request' o 'response'.
    """
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    if kind == "request":
        highlight_request(widget)
    else:
        highlight_response(widget)
    widget.config(state="disabled")
