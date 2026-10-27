import pytest

from quanta.protocol import PeerState, canonical_aad, receiver_candidate_bits


def test_receiver_candidate_bits_use_only_key_rounds_and_flip_singlet_results():
    bob_settings = ["K", "B0", "K", "K"]
    receiver_rows = [
        {"alice_setting": "K", "bob_bit": 1},
        {"alice_setting": "A0", "bob_bit": 0},
        {"alice_setting": "A1", "bob_bit": 1},
        {"alice_setting": "K", "bob_bit": 0},
    ]

    assert receiver_candidate_bits(bob_settings, receiver_rows) == "01"


def test_receiver_candidate_bits_rejects_mismatched_round_counts():
    with pytest.raises(ValueError, match="same number"):
        receiver_candidate_bits(["K"], [])


def test_canonical_aad_is_stable_and_role_specific():
    aad = canonical_aad("session-1", "Alice", "Bob")

    assert aad == (
        b'{"protocol":"assignment2-e91-aes-v1","receiver":"Bob",'
        b'"sender":"Alice","session_id":"session-1"}'
    )
    assert aad != canonical_aad("session-1", "Bob", "Alice")


def test_peer_state_consumes_session_keys_once_and_bounds_message_history():
    state = PeerState(max_sessions=2, max_messages=2)
    state.store_session("one", b"1" * 32)
    state.store_session("two", b"2" * 32)
    state.store_session("three", b"3" * 32)

    assert state.consume_session("one") is None
    assert state.consume_session("two") == b"2" * 32
    assert state.consume_session("two") is None

    state.add_message({"id": "a"})
    state.add_message({"id": "b"})
    state.add_message({"id": "c"})
    assert [item["id"] for item in state.messages()] == ["c", "b"]
