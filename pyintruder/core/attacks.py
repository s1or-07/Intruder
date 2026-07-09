"""Tipos de ataque: generan las asignaciones de payload a posiciones.

Reproduce la semantica de Burp Intruder:
  - Sniper:        un conjunto; ataca cada posicion por turnos.
  - Battering ram: un conjunto; mismo payload en todas las posiciones.
  - Pitchfork:     varios conjuntos; iteracion paralela simultanea.
  - Cluster bomb:  varios conjuntos; todas las combinaciones (producto).
"""

import itertools


def generate_assignments(attack_type, num_positions, payload_sets):
    """Itera (assignment, label).

    assignment: lista de payloads por posicion (None = conservar valor base).
    label:      representacion textual para mostrar en la tabla de resultados.
    """
    attack_type = attack_type.lower()
    if attack_type == "sniper":
        pset = payload_sets[0]
        for pos in range(num_positions):
            for p in pset:
                assignment = [None] * num_positions
                assignment[pos] = p
                yield assignment, f"[pos {pos + 1}] {p}"
    elif attack_type == "battering ram":
        for p in payload_sets[0]:
            yield [p] * num_positions, p
    elif attack_type == "pitchfork":
        for combo in zip(*payload_sets[:num_positions]):
            yield list(combo), " | ".join(combo)
    elif attack_type == "cluster bomb":
        for combo in itertools.product(*payload_sets[:num_positions]):
            yield list(combo), " | ".join(combo)
    else:
        raise ValueError(f"Tipo de ataque desconocido: {attack_type}")


def count_requests(attack_type, num_positions, payload_sets):
    """Calcula cuantas peticiones generara el ataque, sin ejecutarlo."""
    attack_type = attack_type.lower()
    if not payload_sets or not payload_sets[0]:
        return 0
    if attack_type == "sniper":
        return num_positions * len(payload_sets[0])
    if attack_type == "battering ram":
        return len(payload_sets[0])
    sets = [s for s in payload_sets[:num_positions] if s]
    if len(sets) < num_positions:
        return 0
    if attack_type == "pitchfork":
        return min(len(s) for s in sets)
    if attack_type == "cluster bomb":
        total = 1
        for s in sets:
            total *= len(s)
        return total
    return 0
