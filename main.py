import sys

from src.vector_addition import VectorAdditionInit
from src.maximal_independent_set import GreedyMISInit, Status
from src.supervisor import Supervisor


def run_mis(filename, seed=None):
    mis = GreedyMISInit(filename, seed=seed)
    supervisor = Supervisor(mis.nodes, mis)

    print(f"\nSeed used (save this for a reproducible run): {mis.seed}")
    print(f"n = {mis.n}")

    supervisor.run_simulation()

    in_set = sorted(node.id for node in mis.nodes if node.data is Status.IN_MIS)
    print(f"\nSimulation finished in {supervisor.round} round(s).")
    print(f"Maximal independent set found: {in_set}")
    print(f"Matches sequential greedy for the same permutation: {set(in_set) == mis.expected_mis}")


def main():
    va = VectorAdditionInit()  # prompts for n, generates seed + vectors
    supervisor = Supervisor(va.nodes, va)

    print(f"\nSeed used (save this for a reproducible run): {va.seed}")
    print(f"n = {va.n}")
    print("\nInitial vectors:")
    for node in va.nodes:
        print(f"  node {node.id}: {node.data}")

    supervisor.run_simulation()

    print(f"\nSimulation finished in {supervisor.round} round(s).")
    print("Final node values (should match column sums of the original vectors):")
    for node in va.nodes:
        print(f"  node {node.id}: {node.data}  (expected: {va.expected_sum[node.id]})")


if __name__ == "__main__":
    # usage: python main.py               -> vector addition demo
    #        python main.py mis <graph_file> [seed]
    if len(sys.argv) > 1 and sys.argv[1] == "mis":
        run_mis(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    else:
        main()