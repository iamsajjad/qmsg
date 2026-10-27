"""Superdense coding demonstration."""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def _validate_bits(bits: str) -> None:
    if not isinstance(bits, str) or bits not in {"00", "01", "10", "11"}:
        raise ValueError("message must contain exactly two bits: 00, 01, 10, or 11")


def build_superdense_circuit(bits: str) -> QuantumCircuit:
    """Encode two classical bits in Alice's half of an entangled pair."""
    _validate_bits(bits)
    circuit = QuantumCircuit(2, 2)

    circuit.h(0)
    circuit.cx(0, 1)

    if bits[0] == "1":
        circuit.z(0)
    if bits[1] == "1":
        circuit.x(0)

    circuit.cx(0, 1)
    circuit.h(0)

    # Swap the classical destinations so Qiskit's displayed c1c0 string
    # follows the assignment's logical order: phase bit, then flip bit.
    circuit.measure(0, 1)
    circuit.measure(1, 0)
    return circuit


def decode_superdense(
    bits: str,
    shots: int = 100,
    seed: int | None = None,
) -> dict[str, int]:
    """Run ideal superdense coding and return decoded outcome counts."""
    _validate_bits(bits)
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise ValueError("shots must be a positive integer")
    simulator = AerSimulator()
    circuit = transpile(build_superdense_circuit(bits), simulator)
    result = simulator.run(circuit, shots=shots, seed_simulator=seed).result()
    return dict(result.get_counts(circuit))
