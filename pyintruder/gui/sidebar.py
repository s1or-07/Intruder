"""Menu lateral (derecha): tipo de ataque, payloads, opciones y grep."""

from tkinter import filedialog
import tkinter as tk
from tkinter import ttk

from ..constants import COLORS, MONO
from ..core import count_requests

ATTACK_TYPES = ["Sniper", "Battering ram", "Pitchfork", "Cluster bomb"]
MULTI_ATTACKS = ("pitchfork", "cluster bomb")


class Sidebar(ttk.Frame):
    """Configuracion del ataque en un panel lateral compacto."""

    def __init__(self, parent, num_positions_provider):
        super().__init__(parent, width=330)
        self.pack_propagate(False)
        self._num_positions = num_positions_provider
        self._payload_store = {1: "admin\ntest\n' OR '1'='1\n../../etc/passwd\n"}
        self._build()
        self.refresh_payload_sets()

    # ----- construccion ----- #
    def _build(self):
        atk = ttk.LabelFrame(self, text="Ataque")
        atk.pack(fill="x", padx=6, pady=(6, 4))
        ttk.Label(atk, text="Tipo:").grid(row=0, column=0, sticky="w",
                                          padx=4, pady=3)
        self.var_attack = tk.StringVar(value="Sniper")
        cmb = ttk.Combobox(atk, textvariable=self.var_attack, state="readonly",
                           width=16, values=ATTACK_TYPES)
        cmb.grid(row=0, column=1, columnspan=2, sticky="w", padx=2)
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_payload_sets())

        ttk.Label(atk, text="Conjunto:").grid(row=1, column=0, sticky="w",
                                              padx=4, pady=3)
        self.var_set_index = tk.StringVar(value="1")
        self.cmb_set = ttk.Combobox(atk, textvariable=self.var_set_index,
                                    state="readonly", width=5, values=["1"])
        self.cmb_set.grid(row=1, column=1, sticky="w", padx=2)
        self.cmb_set.bind("<<ComboboxSelected>>", lambda e: self._show_set())
        self.lbl_count = ttk.Label(atk, text="Total: 0",
                                   foreground=COLORS["method"])
        self.lbl_count.grid(row=1, column=2, sticky="e", padx=4)

        # Grep y opciones se fijan abajo.
        grep = ttk.LabelFrame(self, text="Grep - Match")
        grep.pack(side="bottom", fill="x", padx=6, pady=(0, 6))
        self.var_grep = tk.StringVar(value="")
        ttk.Entry(grep, textvariable=self.var_grep).pack(fill="x", padx=4, pady=3)
        gopt = ttk.Frame(grep)
        gopt.pack(fill="x", padx=4, pady=(0, 3))
        self.var_grep_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(gopt, text="Regex",
                        variable=self.var_grep_regex).pack(side="left")
        self.var_grep_case = tk.BooleanVar(value=False)
        ttk.Checkbutton(gopt, text="May/min",
                        variable=self.var_grep_case).pack(side="left", padx=8)

        opts = ttk.LabelFrame(self, text="Opciones")
        opts.pack(side="bottom", fill="x", padx=6, pady=4)
        self.var_conc = tk.StringVar(value="5")
        self.var_delay = tk.StringVar(value="0")
        self.var_timeout = tk.StringVar(value="10")
        for i, (lbl, var) in enumerate([("Concurrencia:", self.var_conc),
                                        ("Retardo (ms):", self.var_delay),
                                        ("Timeout (s):", self.var_timeout)]):
            ttk.Label(opts, text=lbl).grid(row=i, column=0, sticky="w",
                                           padx=4, pady=2)
            ttk.Entry(opts, textvariable=var, width=7).grid(
                row=i, column=1, sticky="w", padx=2)
        self.var_update_cl = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Actualizar Content-Length",
                        variable=self.var_update_cl).grid(
                            row=3, column=0, columnspan=2, sticky="w",
                            padx=4, pady=2)

        # Payloads ocupan el espacio central.
        ld = ttk.Frame(self)
        ld.pack(fill="x", padx=6)
        ttk.Label(ld, text="Payloads (uno por linea):").pack(side="left")
        ttk.Button(ld, text="Cargar", width=7,
                   command=self._load_payload_file).pack(side="right")
        ttk.Button(ld, text="Limpiar", width=7,
                   command=self._clear_payload_set).pack(side="right", padx=4)

        pf = ttk.Frame(self)
        pf.pack(fill="both", expand=True, padx=6, pady=(2, 4))
        self.txt_payloads = tk.Text(pf, wrap="none", font=MONO, height=8)
        pys = ttk.Scrollbar(pf, orient="vertical",
                            command=self.txt_payloads.yview)
        self.txt_payloads.configure(yscrollcommand=pys.set)
        self.txt_payloads.pack(side="left", fill="both", expand=True)
        pys.pack(side="right", fill="y")
        self.txt_payloads.insert("1.0", self._payload_store[1])
        self.txt_payloads.bind("<KeyRelease>", lambda e: self._stash_set())

    # ----- API publica ----- #
    def get_attack_type(self):
        return self.var_attack.get()

    def get_payload_sets(self):
        self._stash_current()
        return self._sets_from_store()

    def _sets_from_store(self):
        """Lee los conjuntos desde el almacen, sin re-guardar (evita ciclos)."""
        n = max(1, self._num_positions())
        upto = n if self._is_multi() else 1
        return [[ln for ln in self._payload_store.get(i, "").splitlines() if ln]
                for i in range(1, upto + 1)]

    def get_options(self):
        return {"concurrency": int(self.var_conc.get() or 1),
                "delay": float(self.var_delay.get() or 0),
                "timeout": float(self.var_timeout.get() or 10),
                "update_cl": self.var_update_cl.get()}

    def get_grep(self):
        return {"pattern": self.var_grep.get(),
                "is_regex": self.var_grep_regex.get(),
                "case_sensitive": self.var_grep_case.get()}

    def refresh_payload_sets(self):
        """Reconfigura el selector de conjuntos segun ataque y posiciones."""
        n = max(1, self._num_positions())
        values = [str(i) for i in range(1, n + 1)] if self._is_multi() else ["1"]
        self.cmb_set["values"] = values
        if self.var_set_index.get() not in values:
            self.var_set_index.set("1")
            self._show_set()
        self._update_count()

    # ----- internos ----- #
    def _is_multi(self):
        return self.var_attack.get().lower() in MULTI_ATTACKS

    def _stash_current(self):
        idx = int(self.var_set_index.get())
        self._payload_store[idx] = self.txt_payloads.get("1.0", "end-1c")

    def _stash_set(self):
        self._stash_current()
        self._update_count()

    def _show_set(self):
        idx = int(self.var_set_index.get())
        self.txt_payloads.delete("1.0", "end")
        self.txt_payloads.insert("1.0", self._payload_store.get(idx, ""))
        self._update_count()

    def _clear_payload_set(self):
        self.txt_payloads.delete("1.0", "end")
        self._stash_set()

    def _load_payload_file(self):
        path = filedialog.askopenfilename(title="Cargar wordlist")
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            data = fh.read()
        cur = self.txt_payloads.get("1.0", "end-1c")
        sep = "" if (not cur or cur.endswith("\n")) else "\n"
        self.txt_payloads.insert("end", sep + data)
        self._stash_set()

    def _update_count(self):
        try:
            total = count_requests(self.var_attack.get(),
                                   max(1, self._num_positions()),
                                   self._sets_from_store())
            self.lbl_count.config(text=f"Total: {total}")
        except Exception:
            self.lbl_count.config(text="Total: ?")
