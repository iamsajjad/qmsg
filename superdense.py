"""Run the Assignment 2 superdense coding demonstration."""

import argparse

from quanta.superdense import build_superdense_circuit, decode_superdense


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", choices=("00", "01", "10", "11"), nargs="?", default="11")
    parser.add_argument("--shots", type=int, default=100)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    counts = decode_superdense(args.message, args.shots, args.seed)
    print("Original bits:", args.message)
    print("Decoded counts:", counts)
    print(build_superdense_circuit(args.message).draw(output="text"))


if __name__ == "__main__":
    main()
