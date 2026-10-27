"""Ideal, educational simulation of E91-style entanglement measurements."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import pi
from random import Random
from typing import Sequence

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

ALICE_ANGLES = {"K": 0.0, "A0": 0.0, "A1": pi / 2}
BOB_ANGLES = {"K": 0.0, "B0": pi / 4, "B1": -pi / 4}
CHSH_PAIRS = (("A0", "B0"), ("A0", "B1"), ("A1", "B0"), ("A1", "B1"))


@dataclass(frozen=True, slots=True)
class E91Round:
    index: int
    alice_setting: str
    bob_setting: str
    alice_bit: int
    bob_bit: int


@dataclass(frozen=True, slots=True)
class E91Result:
    rounds: tuple[E91Round, ...]
    chsh: float
    alice_key_bits: str
    bob_key_bits: str
    key_error_rate: float
    chsh_pair_counts: dict[str, int]


def _validate_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def parse_measurement(memory: str) -> tuple[int, int]:
    """Return `(alice_bit, bob_bit)` from Qiskit's `c1c0` memory format."""
    if len(memory) != 2 or any(bit not in "01" for bit in memory):
        raise ValueError("measurement memory must contain exactly two classical bits")
    bob_bit, alice_bit = memory
    return int(alice_bit), int(bob_bit)


def generate_bob_settings(rounds: int, seed: int | None = None) -> list[str]:
    """Generate Bob's independent setting choices."""
    _validate_positive_integer(rounds, "rounds")
    rng = Random(seed)
    labels = tuple(BOB_ANGLES)
    return [rng.choice(labels) for _ in range(rounds)]


def build_e91_circuit(alice_setting: str, bob_setting: str) -> QuantumCircuit:
    """Prepare the singlet state and measure along the requested Bloch angles."""
    if alice_setting not in ALICE_ANGLES:
        raise ValueError(f"unknown Alice setting: {alice_setting}")
    if bob_setting not in BOB_ANGLES:
        raise ValueError(f"unknown Bob setting: {bob_setting}")

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.x(1)
    circuit.z(0)
    circuit.ry(-ALICE_ANGLES[alice_setting], 0)
    circuit.ry(-BOB_ANGLES[bob_setting], 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


def _correlation(rounds: Sequence[E91Round], alice: str, bob: str) -> float:
    selected = [r for r in rounds if r.alice_setting == alice and r.bob_setting == bob]
    if not selected:
        raise ValueError(f"no samples for CHSH pair {alice}/{bob}")
    same = sum(r.alice_bit == r.bob_bit for r in selected)
    different = len(selected) - same
    return (same - different) / len(selected)


def calculate_chsh(rounds: Sequence[E91Round]) -> float:
    """Calculate `|E00 + E01 + E10 - E11|` for the configured settings."""
    e00 = _correlation(rounds, "A0", "B0")
    e01 = _correlation(rounds, "A0", "B1")
    e10 = _correlation(rounds, "A1", "B0")
    e11 = _correlation(rounds, "A1", "B1")
    return abs(e00 + e01 + e10 - e11)


def run_e91(
    rounds: int,
    bob_settings: list[str] | None = None,
    seed: int | None = None,
) -> E91Result:
    """Run an ideal E91-style simulation and return both parties' local keys."""
    _validate_positive_integer(rounds, "rounds")
    if bob_settings is None:
        bob_choices = generate_bob_settings(rounds, None if seed is None else seed + 1)
    else:
        if len(bob_settings) != rounds:
            raise ValueError(f"bob_settings must contain exactly {rounds} entries")
        unknown = next((setting for setting in bob_settings if setting not in BOB_ANGLES), None)
        if unknown is not None:
            raise ValueError(f"unknown Bob setting: {unknown}")
        bob_choices = list(bob_settings)

    rng = Random(seed)
    alice_labels = tuple(ALICE_ANGLES)
    alice_choices = [rng.choice(alice_labels) for _ in range(rounds)]

    grouped_indices: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, pair in enumerate(zip(alice_choices, bob_choices, strict=True)):
        grouped_indices[pair].append(index)

    outcomes: list[tuple[int, int] | None] = [None] * rounds
    simulator = AerSimulator()
    for group_number, ((alice_setting, bob_setting), indices) in enumerate(sorted(grouped_indices.items())):
        circuit = build_e91_circuit(alice_setting, bob_setting)
        compiled = transpile(circuit, simulator, seed_transpiler=seed)
        simulation_seed = None if seed is None else seed + 100 + group_number
        result = simulator.run(
            compiled,
            shots=len(indices),
            memory=True,
            seed_simulator=simulation_seed,
        ).result()
        memory = result.get_memory(compiled)
        for index, sample in zip(indices, memory, strict=True):
            outcomes[index] = parse_measurement(sample)

    measured_rounds = tuple(
        E91Round(index, alice_choices[index], bob_choices[index], *outcome)
        for index, outcome in enumerate(outcomes)
        if outcome is not None
    )
    key_rounds = [r for r in measured_rounds if r.alice_setting == "K" and r.bob_setting == "K"]
    alice_key = "".join(str(r.alice_bit) for r in key_rounds)
    bob_key = "".join(str(1 - r.bob_bit) for r in key_rounds)
    errors = sum(a != b for a, b in zip(alice_key, bob_key, strict=True))
    error_rate = errors / len(alice_key) if alice_key else 0.0

    pair_counts = {
        f"{alice}{bob}": sum(
            r.alice_setting == alice and r.bob_setting == bob for r in measured_rounds
        )
        for alice, bob in CHSH_PAIRS
    }
    try:
        chsh = calculate_chsh(measured_rounds)
    except ValueError:
        chsh = float("nan")

    return E91Result(
        rounds=measured_rounds,
        chsh=chsh,
        alice_key_bits=alice_key,
        bob_key_bits=bob_key,
        key_error_rate=error_rate,
        chsh_pair_counts=pair_counts,
    )
