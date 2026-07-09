"""Plantilla de peticion: parsea marcadores § y genera variantes."""

from ..constants import MARKER


class RequestTemplate:
    """Parsea una peticion cruda con marcadores § y construye variantes.

    Cada par de marcadores § define una posicion de payload. El texto encerrado
    entre el par es el "valor base", que se sustituye al asignar un payload.
    """

    def __init__(self, raw: str):
        self.raw = raw
        self.segments, self.base_values = self._parse(raw)
        self.num_positions = len(self.base_values)

    @staticmethod
    def _parse(raw: str):
        parts = raw.split(MARKER)
        if (len(parts) - 1) % 2 != 0:
            raise ValueError(
                "Numero impar de marcadores §. Cada posicion necesita un par.")
        segments = [parts[0]]
        base_values = []
        i = 1
        while i < len(parts):
            base_values.append(parts[i])       # texto base entre el par §
            segments.append(parts[i + 1])      # literal hasta el siguiente par
            i += 2
        return segments, base_values

    def build(self, assignment):
        """Construye la peticion final.

        assignment: lista de longitud num_positions; cada elemento es el payload
        (str) de esa posicion, o None para conservar el valor base (posiciones
        no atacadas en Sniper).
        """
        out = [self.segments[0]]
        for idx, base in enumerate(self.base_values):
            value = assignment[idx]
            out.append(base if value is None else value)
            out.append(self.segments[idx + 1])
        return "".join(out)
