"""Pestana de resultados: tabla ordenable + visores de request/response."""

import tkinter as tk
from tkinter import ttk

from ..constants import COLORS, MONO
from .highlighting import configure_http_tags, set_viewer

COLUMNS = ("idx", "payload", "status", "length", "time", "grep", "error")
HEADERS = {"idx": "#", "payload": "Payload", "status": "Estado",
           "length": "Longitud", "time": "Tiempo (ms)",
           "grep": "Grep", "error": "Error"}
WIDTHS = {"idx": 50, "payload": 340, "status": 70, "length": 90,
          "time": 90, "grep": 60, "error": 200}
NUMERIC = {"idx", "status", "length", "time", "grep"}


class ResultsPanel(ttk.Frame):
    """Tabla de resultados y visores coloreados de la peticion y la respuesta."""

    def __init__(self, parent):
        super().__init__(parent)
        self._result_map = {}
        self._sort_state = {}
        self._build()

    # ----- construccion ----- #
    def _build(self):
        paned = ttk.Panedwindow(self, orient="vertical")
        paned.pack(fill="both", expand=True, padx=4, pady=4)

        top = ttk.Frame(paned)
        paned.add(top, weight=2)
        tw = ttk.Frame(top)
        tw.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tw, columns=COLUMNS, show="headings")
        for c in COLUMNS:
            self.tree.heading(c, text=HEADERS[c],
                              command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=WIDTHS[c],
                             anchor="w" if c == "payload" else "center")
        tvs = ttk.Scrollbar(tw, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tvs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tvs.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.tag_configure("hit", background=COLORS["hit_bg"])

        self.lbl_progress = ttk.Label(top, text="Enviadas 0 / 0")
        self.lbl_progress.pack(anchor="w", pady=2)

        bottom = ttk.Panedwindow(paned, orient="horizontal")
        paned.add(bottom, weight=3)
        self.txt_req_view = self._make_viewer(bottom, "Request enviado")
        self.txt_resp_view = self._make_viewer(bottom, "Response recibido")

    def _make_viewer(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title)
        parent.add(frame, weight=1)
        txt = tk.Text(frame, wrap="word", font=MONO, state="disabled",
                      background=COLORS["viewer_bg"])
        ys = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=ys.set)
        txt.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        configure_http_tags(txt)
        return txt

    # ----- API publica ----- #
    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._result_map.clear()
        set_viewer(self.txt_req_view, "", "request")
        set_viewer(self.txt_resp_view, "", "response")
        self.lbl_progress.config(text="Enviadas 0 / 0")

    def add_result(self, r):
        iid = str(r["idx"])
        self._result_map[iid] = r
        tags = ("hit",) if (r["grep"] not in ("", "0")) else ()
        self.tree.insert("", "end", iid=iid, tags=tags, values=(
            r["idx"], r["payload"], r["status"], r["length"],
            r["time"], r["grep"], r["error"]))

    def set_progress(self, received, total):
        self.lbl_progress.config(text=f"Enviadas {received} / {total}")

    # ----- internos ----- #
    def _on_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        r = self._result_map.get(sel[0])
        if not r:
            return
        set_viewer(self.txt_req_view, r.get("request", ""), "request")
        resp = r.get("response", "")
        if not resp and r.get("error"):
            resp = f"[Sin respuesta] Error: {r['error']}"
        set_viewer(self.txt_resp_view, resp, "response")

    def _sort_by(self, col):
        reverse = self._sort_state.get(col, False)

        def key(item):
            v = self.tree.set(item, col)
            if col in NUMERIC:
                try:
                    return float(v)
                except ValueError:
                    return float("-inf")
            return v

        items = list(self.tree.get_children(""))
        items.sort(key=key, reverse=reverse)
        for i, item in enumerate(items):
            self.tree.move(item, "", i)
        self._sort_state[col] = not reverse
