"""Authenticate and decrypt an Assignment 2 AES-GCM message."""

import argparse
import json
from pathlib import Path

from quanta.crypto import EncryptedPayload, decrypt_message, derive_aes_key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path, default=Path("e91_key.txt"))
    parser.add_argument("--input", type=Path, default=Path("encrypted.bin"))
    args = parser.parse_args()

    candidate_bits = args.key_file.read_text(encoding="ascii").strip()
    envelope = json.loads(args.input.read_bytes().decode("ascii"))
    salt = bytes.fromhex(envelope["salt"])
    aad = bytes.fromhex(envelope["aad"])
    payload = EncryptedPayload.from_dict(envelope)
    key = derive_aes_key(candidate_bits, salt)
    plaintext = decrypt_message(key, payload, aad)
    print("Decrypted message:", plaintext.decode("utf-8"))


if __name__ == "__main__":
    main()
