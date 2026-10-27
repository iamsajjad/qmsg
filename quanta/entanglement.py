"""Bell-state construction and ideal measurement helpers."""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def build_phi_plus_circuit(measure: bool = True) -> QuantumCircuit:
    """Build a circuit that prepares |Phi+> = (|00> + |11>) / sqrt(2)."""
    circuit = QuantumCircuit(2, 2 if measure else 0)
    circuit.h(0)
    circuit.cx(0, 1)
    if measure:
        circuit.measure([0, 1], [0, 1])
    return circuit


def measure_phi_plus(shots: int, seed: int | None = None) -> dict[str, int]:
    """Measure an ideal |Phi+> state and return Qiskit outcome counts."""
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise ValueError("shots must be a positive integer")

    simulator = AerSimulator()
    circuit = transpile(build_phi_plus_circuit(), simulator)
    result = simulator.run(
        circuit,
        shots=shots,
        seed_simulator=seed,
    ).result()
    return dict(result.get_counts(circuit))
