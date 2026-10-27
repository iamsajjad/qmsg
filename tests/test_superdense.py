import pytest

from quanta.superdense import build_superdense_circuit, decode_superdense


@pytest.mark.parametrize("bits", ["00", "01", "10", "11"])
def test_all_superdense_messages_decode_exactly(bits):
    counts = decode_superdense(bits, shots=128, seed=5)

    assert counts == {bits: 128}


def test_superdense_circuit_contains_encoding_and_decoding_operations():
    circuit = build_superdense_circuit("11")
    operations = circuit.count_ops()

    assert circuit.num_qubits == 2
    assert circuit.num_clbits == 2
    assert operations["h"] == 2
    assert operations["cx"] == 2
    assert operations["z"] == 1
    assert operations["x"] == 1
    assert operations["measure"] == 2


@pytest.mark.parametrize("bits", ["", "0", "000", "12", 11, None])
def test_superdense_rejects_invalid_messages(bits):
    with pytest.raises(ValueError, match="two bits"):
        build_superdense_circuit(bits)
