"""Encrypt a message with an E91 candidate key using AES-256-GCM."""

import argparse
import json
from pathlib import Path
import secrets

from quanta.crypto import derive_aes_key, encrypt_message


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", nargs="?", default="Hello Bob, this message is secret!")
    parser.add_argument("--key-file", type=Path, default=Path("e91_key.txt"))
    parser.add_argument("--output", type=Path, default=Path("encrypted.bin"))
    args = parser.parse_args()

    candidate_bits = args.key_file.read_text(encoding="ascii").strip()
    salt = secrets.token_bytes(16)
    aad = b"assignment2-e91-aes-file-v1"
    key = derive_aes_key(candidate_bits, salt)
    payload = encrypt_message(key, args.message.encode("utf-8"), aad)
    envelope = {
        "salt": salt.hex(),
        "aad": aad.hex(),
        **payload.to_dict(),
    }
    args.output.write_bytes(json.dumps(envelope, separators=(",", ":")).encode("ascii"))

    print("Original message:", args.message)
    print("Nonce:", payload.nonce.hex())
    print("Encrypted message:", payload.ciphertext.hex())
    print("Saved to:", args.output)


if __name__ == "__main__":
    main()
