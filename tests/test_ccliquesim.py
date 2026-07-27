from src.ccliquesim import *
from src import maximal_independent_set as mis

if __name__ == "__main__":
    print("Running Tree sims")
    sim = CCSim(mis.GreedyMISInit, 1000, "src/graph_tree_1000.txt", "output/tree_n1000_s1000.csv")
    sim.run_sims()
    print("Running KMW sims")
    sim = CCSim(mis.GreedyMISInit, 1000, "src/graph_kmw_1000.txt", "output/KMW_n1000_s1000.csv")
    sim.run_sims()
    print("Running scale free sims")
    sim = CCSim(mis.GreedyMISInit, 1000, "src/graph_scale_free_1000.txt", "output/scale_free_n1000_s1000.csv")
    sim.run_sims()
