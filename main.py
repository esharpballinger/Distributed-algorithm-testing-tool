from src.vector_addition import VectorAddition
from src.supervisor import Supervisor

def main():
    va = VectorAddition()  # prompts for n, generates seed + vectors
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
    main()