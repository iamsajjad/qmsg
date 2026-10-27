from math import isclose

import pytest

from quanta.e91 import (
    E91Round,
    calculate_chsh,
    generate_bob_settings,
    parse_measurement,
    run_e91,
)


def test_qiskit_memory_is_parsed_as_bob_then_alice():
    assert parse_measurement("10") == (0, 1)
    assert parse_measurement("01") == (1, 0)


@pytest.mark.parametrize("memory", ["", "0", "000", "ab", "0 1"])
def test_parse_measurement_rejects_invalid_memory(memory):
    with pytest.raises(ValueError, match="two classical bits"):
        parse_measurement(memory)


def test_chsh_uses_expected_sign_convention():
    rounds = [
        E91Round(0, "A0", "B0", 0, 1),
        E91Round(1, "A0", "B1", 0, 1),
        E91Round(2, "A1", "B0", 0, 1),
        E91Round(3, "A1", "B1", 0, 0),
    ]

    assert calculate_chsh(rounds) == pytest.approx(4.0)


def test_seeded_ideal_e91_run_violates_chsh_and_produces_matching_keys():
    result = run_e91(rounds=4096, seed=19)

    assert result.chsh > 2.5
    assert result.chsh < 3.1
    assert len(result.alice_key_bits) >= 256
    assert result.alice_key_bits == result.bob_key_bits
    assert isclose(result.key_error_rate, 0.0, abs_tol=1e-12)
    assert set(result.alice_key_bits) <= {"0", "1"}
    assert all(result.chsh_pair_counts[pair] > 100 for pair in ("A0B0", "A0B1", "A1B0", "A1B1"))


def test_supplied_bob_settings_are_used_without_mutation():
    bob_settings = ["K"] * 96

    result = run_e91(rounds=96, bob_settings=bob_settings, seed=3)

    assert [round_.bob_setting for round_ in result.rounds] == bob_settings
    assert bob_settings == ["K"] * 96
    assert result.alice_key_bits == result.bob_key_bits


def test_generate_bob_settings_is_seeded_and_valid():
    first = generate_bob_settings(32, seed=11)
    second = generate_bob_settings(32, seed=11)

    assert first == second
    assert len(first) == 32
    assert set(first) <= {"K", "B0", "B1"}


@pytest.mark.parametrize("rounds", [0, -2, True, 3.5])
def test_run_e91_rejects_invalid_round_count(rounds):
    with pytest.raises(ValueError, match="positive integer"):
        run_e91(rounds=rounds)


def test_run_e91_rejects_invalid_supplied_settings():
    with pytest.raises(ValueError, match="exactly 8"):
        run_e91(rounds=8, bob_settings=["K"] * 7)

    with pytest.raises(ValueError, match="unknown Bob setting"):
        run_e91(rounds=8, bob_settings=["K"] * 7 + ["not-a-basis"])
