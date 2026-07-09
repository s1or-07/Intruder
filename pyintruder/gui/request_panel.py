"""Panel izquierdo: editor de la peticion base y datos del objetivo."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..constants import MARKER, MONO
from ..core import parse_raw_request
from .highlighting import configure_http_tags, highlight_request

SAMPLE_REQUEST = (
    "GET /search?q=" + MARKER + "test" + MARKER + " HTTP/1.1\n"
    "Host: example.com\n"
    "User-Agent: PyIntruder\n"
    "Accept: */*\n"
    "Connection: close\n"
)


class RequestPanel(ttk.Frame):
    """Editor de la peticion con coloreado y marcado de posiciones §."""

    def __init__(self, parent, on_positions_changed=None):
        super().__init__(parent)
        self.on_positions_changed = on_positions_changed
        self._build()
        highlight_request(self.txt_request)
        self._refresh_positions()

    # ----- construccion ----- #
    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=4, pady=6)
        ttk.Label(top, text="Host:").pack(side="left")
        self.var_host = tk.StringVar(value="example.com")
        ttk.Entry(top, textvariable=self.var_host, width=24).pack(
            side="left", padx=(2, 10))
        ttk.Label(top, text="Puerto:").pack(side="left")
        self.var_port = tk.StringVar(value="80")
        ttk.Entry(top, textvariable=self.var_port, width=6).pack(
            side="left", padx=(2, 10))
        self.var_tls = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="HTTPS", variable=self.var_tls,
                        command=self._on_tls_toggle).pack(side="left")
        ttk.Button(top, text="Auto", width=6,
                   command=self._autofill_target).pack(side="left", padx=8)

        ttk.Label(self, text=("Peticion base (marca posiciones con § usando "
                              "'Marcar §'):")).pack(anchor="w", padx=4)

        editor = ttk.Frame(self)
        editor.pack(fill="both", expand=True, padx=4, pady=2)
        self.txt_request = tk.Text(editor, wrap="none", undo=True, font=MONO)
        ys = ttk.Scrollbar(editor, orient="vertical",
                           command=self.txt_request.yview)
        xs = ttk.Scrollbar(self, orient="horizontal",
                           command=self.txt_request.xview)
        self.txt_request.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.txt_request.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        xs.pack(fill="x", padx=4)
        self.txt_request.insert("1.0", SAMPLE_REQUEST)
        configure_http_tags(self.txt_request)
        self.txt_request.bind("<KeyRelease>", self._on_change)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=4, pady=4)
        ttk.Button(btns, text="Marcar §",
                   command=self._add_marker).pack(side="left")
        ttk.Button(btns, text="Limpiar §",
                   command=self._clear_markers).pack(side="left", padx=6)
        ttk.Button(btns, text="Cargar peticion...",
                   command=self._load_request).pack(side="left")
        self.lbl_positions = ttk.Label(btns, text="Posiciones: 0")
        self.lbl_positions.pack(side="right")

    # ----- API publica ----- #
    def get_raw(self):
        return self.txt_request.get("1.0", "end-1c")

    def num_positions(self):
        return self.get_raw().count(MARKER) // 2

    def get_host(self):
        return self.var_host.get().strip()

    def get_port(self):
        return self.var_port.get().strip()

    def get_tls(self):
        return self.var_tls.get()

    # ----- callbacks internos ----- #
    def _on_change(self, _evt=None):
        highlight_request(self.txt_request)
        self._refresh_positions()

    def _refresh_positions(self):
        self.lbl_positions.config(text=f"Posiciones: {self.num_positions()}")
        if self.on_positions_changed:
            self.on_positions_changed()

    def _add_marker(self):
        try:
            sel = self.txt_request.get("sel.first", "sel.last")
            self.txt_request.delete("sel.first", "sel.last")
            self.txt_request.insert("insert", MARKER + sel + MARKER)
        except tk.TclError:
            messagebox.showinfo("Marcar", "Selecciona primero el texto a marcar.")
        self._on_change()

    def _clear_markers(self):
        content = self.get_raw().replace(MARKER, "")
        self.txt_request.delete("1.0", "end")
        self.txt_request.insert("1.0", content)
        self._on_change()

    def _autofill_target(self):
        _m, _p, headers, _b = parse_raw_request(self.get_raw())
        host = headers.get("Host", "")
        if not host:
            messagebox.showinfo("Auto", "No se encontro cabecera Host.")
            return
        if ":" in host:
            h, p = host.rsplit(":", 1)
            self.var_host.set(h)
            self.var_port.set(p)
        else:
            self.var_host.set(host)
            self.var_port.set("443" if self.var_tls.get() else "80")

    def _on_tls_toggle(self):
        if self.var_port.get() in ("80", "443"):
            self.var_port.set("443" if self.var_tls.get() else "80")

    def _load_request(self):
        path = filedialog.askopenfilename(title="Cargar peticion cruda")
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            self.txt_request.delete("1.0", "end")
            self.txt_request.insert("1.0", fh.read())
        self._on_change()
