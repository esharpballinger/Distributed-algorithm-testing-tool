import sys
import webbrowser
from pathlib import Path

from src.vector_addition import VectorAdditionInit
from src.maximal_independent_set import GreedyMISInit, Status
from src.mis_visualization import run_with_history, write_html
from src.supervisor import Supervisor

DEFAULT_GRAPH = "src/goober.txt"
OUTPUT_HTML = "mis_run.html"


def main(filename=DEFAULT_GRAPH, seed=None):
    mis = GreedyMISInit(filename, seed=seed)

    print(f"\nSeed used (save this for a reproducible run): {mis.seed}")
    print(f"n = {mis.n}")

    supervisor, history, messages = run_with_history(mis)

    in_set = sorted(node.id for node in mis.nodes if node.data is Status.IN_MIS)
    print(f"\nSimulation finished in {supervisor.round} round(s).")
    print(f"Maximal independent set found: {in_set}")
    print(f"Matches sequential greedy for the same permutation: {set(in_set) == mis.expected_mis}")

    write_html(mis, history, messages, OUTPUT_HTML)
    path = Path(OUTPUT_HTML).resolve()
    print(f"\nRound-by-round visualization written to {path}")
    webbrowser.open(path.as_uri())


def run_vector_addition():
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
    # usage: python main.py [graph_file] [seed]   -> MIS with visualization
    #        python main.py va                    -> vector addition demo
    if len(sys.argv) > 1 and sys.argv[1] == "va":
        run_vector_addition()
    else:
        main(
            sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GRAPH,
            int(sys.argv[2]) if len(sys.argv) > 2 else None,
        )
