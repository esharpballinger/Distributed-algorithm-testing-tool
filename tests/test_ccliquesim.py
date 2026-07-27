from src.ccliquesim import *
from src import maximal_independent_set as mis

if __name__ == "__main__":
    sim = CCSim(mis.GreedyMISInit, 10, "src/goober.txt", "output/goober.csv")
    sim.run_sims()
