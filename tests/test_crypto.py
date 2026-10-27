import os

import pytest
from cryptography.exceptions import InvalidTag

from quanta.crypto import (
    EncryptedPayload,
    decrypt_message,
    derive_aes_key,
    encrypt_message,
    pack_bits,
)


def test_pack_bits_preserves_exact_bit_length():
    assert pack_bits("101") == b"\x00\x00\x00\x03\xa0"
    assert pack_bits("00000001") == b"\x00\x00\x00\x08\x01"


@pytest.mark.parametrize("bits", ["", "1021", "hello"])
def test_pack_bits_rejects_invalid_input(bits):
    with pytest.raises(ValueError):
        pack_bits(bits)


def test_matching_candidate_bits_derive_equal_256_bit_keys():
    bits = "01" * 128
    salt = bytes.fromhex("00112233445566778899aabbccddeeff")

    alice_key = derive_aes_key(bits, salt)
    bob_key = derive_aes_key(bits, salt)

    assert alice_key == bob_key
    assert len(alice_key) == 32


def test_different_salts_derive_different_keys():
    bits = "01" * 128

    first = derive_aes_key(bits, b"a" * 16)
    second = derive_aes_key(bits, b"b" * 16)

    assert first != second


def test_key_derivation_rejects_short_candidate_key():
    with pytest.raises(ValueError, match="at least 256 bits"):
        derive_aes_key("01" * 127, b"s" * 16)


def test_aes_gcm_round_trip_and_json_serialization():
    key = bytes(range(32))
    aad = b'{"protocol":"assignment2-v1","session":"abc"}'

    payload = encrypt_message(key, b"Hello Bob", aad)
    restored = EncryptedPayload.from_dict(payload.to_dict())

    assert decrypt_message(key, restored, aad) == b"Hello Bob"
    assert len(payload.nonce) == 12
    assert len(payload.ciphertext) == len(b"Hello Bob") + 16
    assert set(payload.to_dict()) == {"nonce", "ciphertext"}


def test_encryption_uses_a_fresh_nonce():
    key = os.urandom(32)

    first = encrypt_message(key, b"same", b"context")
    second = encrypt_message(key, b"same", b"context")

    assert first.nonce != second.nonce
    assert first.ciphertext != second.ciphertext


@pytest.mark.parametrize("changed", ["ciphertext", "nonce", "aad", "key"])
def test_aes_gcm_rejects_tampering(changed):
    key = bytes(range(32))
    aad = b"session-metadata"
    payload = encrypt_message(key, b"authenticated message", aad)
    tampered_key = key
    tampered_aad = aad
    tampered_payload = payload

    if changed == "ciphertext":
        altered = bytes([payload.ciphertext[0] ^ 1]) + payload.ciphertext[1:]
        tampered_payload = EncryptedPayload(payload.nonce, altered)
    elif changed == "nonce":
        altered = bytes([payload.nonce[0] ^ 1]) + payload.nonce[1:]
        tampered_payload = EncryptedPayload(altered, payload.ciphertext)
    elif changed == "aad":
        tampered_aad = aad + b"!"
    else:
        tampered_key = bytes([key[0] ^ 1]) + key[1:]

    with pytest.raises(InvalidTag):
        decrypt_message(tampered_key, tampered_payload, tampered_aad)
