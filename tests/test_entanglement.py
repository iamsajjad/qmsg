import pytest

from quanta.entanglement import build_phi_plus_circuit, measure_phi_plus


def test_phi_plus_circuit_contains_two_qubits_and_measurements():
    circuit = build_phi_plus_circuit(measure=True)

    assert circuit.num_qubits == 2
    assert circuit.num_clbits == 2
    assert circuit.count_ops()["h"] == 1
    assert circuit.count_ops()["cx"] == 1
    assert circuit.count_ops()["measure"] == 2


def test_ideal_phi_plus_measurements_are_correlated():
    counts = measure_phi_plus(shots=256, seed=7)

    assert set(counts) <= {"00", "11"}
    assert sum(counts.values()) == 256
    assert counts["00"] > 0
    assert counts["11"] > 0


@pytest.mark.parametrize("shots", [0, -1, True, 1.5])
def test_measure_phi_plus_rejects_invalid_shots(shots):
    with pytest.raises(ValueError, match="positive integer"):
        measure_phi_plus(shots=shots)
