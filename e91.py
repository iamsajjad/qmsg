"""Run the Assignment 2 E91 simulation."""

import argparse
from pathlib import Path

from quanta.e91 import run_e91


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=4096)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--key-out", type=Path)
    args = parser.parse_args()

    result = run_e91(args.rounds, seed=args.seed)
    print(f"CHSH S: {result.chsh:.4f}")
    print(f"Candidate key bits: {len(result.alice_key_bits)}")
    print(f"Key error rate: {result.key_error_rate:.2%}")
    print(f"Alice and Bob keys match: {result.alice_key_bits == result.bob_key_bits}")
    if args.key_out is not None:
        args.key_out.write_text(result.alice_key_bits + "\n", encoding="ascii")
        print(f"Candidate key written to: {args.key_out}")


if __name__ == "__main__":
    main()
