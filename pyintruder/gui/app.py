"""Ventana principal: ensambla los paneles y gestiona el ciclo del ataque."""

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from ..constants import COLORS
from ..core import AttackEngine, RequestTemplate, count_requests
from .request_panel import RequestPanel
from .results_panel import ResultsPanel
from .sidebar import Sidebar


class PyIntruderApp(tk.Tk):
    """Aplicacion principal de PyIntruder."""

    def __init__(self):
        super().__init__()
        self.title("PyIntruder - HTTP Request Fuzzer")
        self.geometry("1180x800")
        self.minsize(980, 660)
        self.engine = None
        self._ui_queue = queue.Queue()
        self._total = 0
        self._received = 0
        self._build()
        self.after(80, self._drain_ui_queue)

    # ----- construccion ----- #
    def _build(self):
        # self._build_banner()
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        tab_main = ttk.Frame(nb)
        tab_results = ttk.Frame(nb)
        nb.add(tab_main, text="1. Peticion y ataque")
        nb.add(tab_results, text="2. Resultados")

        paned = ttk.Panedwindow(tab_main, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=4, pady=4)
        self.request_panel = RequestPanel(paned)
        self.sidebar = Sidebar(paned, self.request_panel.num_positions)
        paned.add(self.request_panel, weight=3)
        paned.add(self.sidebar, weight=1)
        # Al cambiar las posiciones, el menu lateral se refresca.
        self.request_panel.on_positions_changed = self.sidebar.refresh_payload_sets

        self.results_panel = ResultsPanel(tab_results)
        self.results_panel.pack(fill="both", expand=True)

        self._build_controls()
        self.sidebar.refresh_payload_sets()

    def _build_banner(self):
        bar = tk.Frame(self, bg=COLORS["banner_bg"])
        bar.pack(fill="x")
        tk.Label(
            bar,
            text=("  AVISO: no me hago responsable chele "
                  "Usalo para apredender a hacer el tuyo "),
            bg=COLORS["banner_bg"], fg="white", anchor="w",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(fill="x", padx=4, pady=3)

    def _build_controls(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        self.btn_start = ttk.Button(bar, text="Iniciar ataque",
                                    command=self._start_attack)
        self.btn_start.pack(side="left")
        self.btn_stop = ttk.Button(bar, text="Detener", state="disabled",
                                   command=self._stop_attack)
        self.btn_stop.pack(side="left", padx=6)
        self.lbl_status = ttk.Label(bar, text="Listo.")
        self.lbl_status.pack(side="left", padx=12)

    # ----- ciclo del ataque ----- #
    def _start_attack(self):
        raw = self.request_panel.get_raw()
        try:
            template = RequestTemplate(raw)
        except ValueError as e:
            messagebox.showerror("Peticion invalida", str(e))
            return
        if template.num_positions == 0:
            messagebox.showerror("Sin posiciones",
                                 "Marca al menos una posicion con §.")
            return

        attack = self.sidebar.get_attack_type()
        sets = self.sidebar.get_payload_sets()
        if attack.lower() in ("pitchfork", "cluster bomb") and \
                len(sets) < template.num_positions:
            messagebox.showerror("Payloads insuficientes",
                                 "Pitchfork/Cluster bomb necesitan un conjunto "
                                 "por posicion.")
            return
        if any(not s for s in sets):
            messagebox.showerror("Lista vacia",
                                 "Algun conjunto de payloads esta vacio.")
            return

        options = self.sidebar.get_options()
        try:
            host = self.request_panel.get_host()
            port = int(self.request_panel.get_port())
            timeout = float(options["timeout"])
        except ValueError:
            messagebox.showerror("Datos invalidos", "Revisa host/puerto/timeout.")
            return
        if not host:
            messagebox.showerror("Host", "Indica el host de destino.")
            return

        total = count_requests(attack, template.num_positions, sets)
        if not messagebox.askyesno(
            "Confirmar ataque",
            f"Destino: {host}:{port}\nTipo: {attack}\n"
            f"Peticiones a enviar: {total}\n\n"
            "Confirma que tienes AUTORIZACION para probar este objetivo.\n"
            "¿Iniciar?",
        ):
            return

        self.results_panel.clear()
        self._total = total
        self._received = 0
        self.results_panel.set_progress(0, total)

        target = {"host": host, "port": port,
                  "tls": self.request_panel.get_tls(), "timeout": timeout}
        self.engine = AttackEngine(
            template, attack, sets, target, options, self.sidebar.get_grep(),
            result_cb=lambda r: self._ui_queue.put(("result", r)),
            done_cb=lambda stopped: self._ui_queue.put(("done", stopped)))
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="Ataque en curso...")
        self.engine.start()

    def _stop_attack(self):
        if self.engine:
            self.engine.stop()
        self.lbl_status.config(text="Deteniendo...")

    # ----- cola UI (segura para el hilo principal) ----- #
    def _drain_ui_queue(self):
        try:
            while True:
                kind, payload = self._ui_queue.get_nowait()
                if kind == "result":
                    self._received += 1
                    self.results_panel.add_result(payload)
                    self.results_panel.set_progress(self._received, self._total)
                elif kind == "done":
                    self._on_done(payload)
        except queue.Empty:
            pass
        self.after(80, self._drain_ui_queue)

    def _on_done(self, stopped):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(
            text="Detenido por el usuario." if stopped else "Ataque completado.")


def main():
    PyIntruderApp().mainloop()
