"""Motor del ataque: ejecuta el envio de forma concurrente y con control
de velocidad, notificando cada resultado mediante callbacks."""

import queue
import re
import threading
import time

from .attacks import generate_assignments
from .http_client import send_request


class AttackEngine:
    """Orquesta el envio de todas las variantes generadas por el ataque.

    Callbacks:
      result_cb(result_dict) -> se invoca por cada peticion completada.
      done_cb(stopped: bool) -> se invoca al terminar (stopped=True si se
                                detuvo manualmente).
    Ambos callbacks se ejecutan en hilos de trabajo; el consumidor (la GUI)
    debe encolarlos de forma segura para el hilo principal.
    """

    def __init__(self, template, attack_type, payload_sets, target, options,
                 grep, result_cb, done_cb):
        self.template = template
        self.attack_type = attack_type
        self.payload_sets = payload_sets
        self.target = target            # host, port, tls, timeout
        self.options = options          # concurrency, delay, update_cl
        self.grep = grep                # pattern, is_regex, case_sensitive
        self.result_cb = result_cb
        self.done_cb = done_cb
        self._stop = threading.Event()
        self._jobs = queue.Queue()
        self._compiled_grep = self._compile_grep()

    def _compile_grep(self):
        pat = self.grep.get("pattern", "").strip()
        if not pat:
            return None
        flags = 0 if self.grep.get("case_sensitive") else re.IGNORECASE
        try:
            return re.compile(pat if self.grep.get("is_regex")
                              else re.escape(pat), flags)
        except re.error:
            return None

    def _grep_count(self, text):
        if self._compiled_grep is None or not text:
            return ""
        return str(len(self._compiled_grep.findall(text)))

    def stop(self):
        self._stop.set()

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        gen = generate_assignments(
            self.attack_type, self.template.num_positions, self.payload_sets)
        for idx, (assignment, label) in enumerate(gen, start=1):
            if self._stop.is_set():
                break
            self._jobs.put((idx, assignment, label))

        n = max(1, int(self.options.get("concurrency", 5)))
        threads = [threading.Thread(target=self._worker, daemon=True)
                   for _ in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.done_cb(self._stop.is_set())

    def _worker(self):
        delay = float(self.options.get("delay", 0)) / 1000.0
        while not self._stop.is_set():
            try:
                idx, assignment, label = self._jobs.get_nowait()
            except queue.Empty:
                return
            raw = self.template.build(assignment)
            res = send_request(
                raw, self.target["host"], self.target["port"],
                self.target["tls"], self.target["timeout"],
                self.options.get("update_cl", True))
            self.result_cb({
                "idx": idx,
                "payload": label,
                "status": "" if res["status"] is None else res["status"],
                "length": res["length"],
                "time": round(res["elapsed"], 1),
                "grep": self._grep_count(res["response"]),
                "error": res["error"] or "",
                "request": raw,
                "response": res["response"],
            })
            if delay:
                time.sleep(delay)
