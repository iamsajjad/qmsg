"""Key derivation and AES-GCM helpers for the educational E91 demo."""

from __future__ import annotations

from dataclasses import dataclass
import secrets

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


@dataclass(frozen=True, slots=True)
class EncryptedPayload:
    nonce: bytes
    ciphertext: bytes

    def to_dict(self) -> dict[str, str]:
        return {"nonce": self.nonce.hex(), "ciphertext": self.ciphertext.hex()}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "EncryptedPayload":
        try:
            nonce = bytes.fromhex(data["nonce"])
            ciphertext = bytes.fromhex(data["ciphertext"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("payload must contain hexadecimal nonce and ciphertext") from exc
        if len(nonce) != 12:
            raise ValueError("AES-GCM nonce must be 12 bytes")
        if len(ciphertext) < 16:
            raise ValueError("AES-GCM ciphertext must include a 16-byte tag")
        return cls(nonce=nonce, ciphertext=ciphertext)


def pack_bits(bits: str) -> bytes:
    """Pack a binary string with a four-byte prefix that preserves its bit length."""
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("bits must be a non-empty string containing only 0 and 1")
    byte_count = (len(bits) + 7) // 8
    padding = byte_count * 8 - len(bits)
    packed = (int(bits, 2) << padding).to_bytes(byte_count, "big")
    return len(bits).to_bytes(4, "big") + packed


def derive_aes_key(
    bits: str,
    salt: bytes,
    info: bytes = b"assignment2-e91-aes-v1",
) -> bytes:
    """Derive a 32-byte AES key from at least 256 candidate key bits."""
    if len(bits) < 256:
        raise ValueError("candidate key must contain at least 256 bits")
    if not isinstance(salt, bytes) or len(salt) < 16:
        raise ValueError("salt must contain at least 16 bytes")
    if not isinstance(info, bytes) or not info:
        raise ValueError("info must be non-empty bytes")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    ).derive(pack_bits(bits))


def encrypt_message(key: bytes, plaintext: bytes, aad: bytes) -> EncryptedPayload:
    """Encrypt and authenticate a message with a fresh 96-bit nonce."""
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    return EncryptedPayload(nonce=nonce, ciphertext=ciphertext)


def decrypt_message(key: bytes, payload: EncryptedPayload, aad: bytes) -> bytes:
    """Authenticate and decrypt an AES-GCM payload."""
    return AESGCM(key).decrypt(payload.nonce, payload.ciphertext, aad)
