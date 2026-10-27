"""Run the Assignment 2 Bell-state demonstration."""

import argparse

from quanta.entanglement import build_phi_plus_circuit, measure_phi_plus


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    counts = measure_phi_plus(args.shots, args.seed)
    print("Measurement results:")
    print(counts)
    print(build_phi_plus_circuit().draw(output="text"))


if __name__ == "__main__":
    main()
