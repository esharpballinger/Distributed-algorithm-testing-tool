import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src import maximal_independent_set as mis
from src.supervisor import Supervisor

def generate_regular_test_graph(n, delta, filename):
    """
    Generates a deterministic regular-like graph structure where every node 
    has degree bounded strictly by Delta, avoiding cascading tree deformations.
    """
    adj = {i: set() for i in range(n)}
    # Construct a stable ring lattice where each node connects to delta neighbors
    for i in range(n):
        for j in range(1, (delta // 2) + 1):
            neighbor_right = (i + j) % n
            neighbor_left = (i - j) % n
            adj[i].add(neighbor_right)
            adj[i].add(neighbor_left)
            
    os.makedirs("src/temp_graphs", exist_ok=True)
    filepath = f"src/temp_graphs/{filename}"
    with open(filepath, 'w') as f:
        f.write(f"{n}\n")
        for i in range(n):
            neighbors = sorted(list(adj[i]))
            f.write(" ".join(map(str, neighbors)) + "\n")
            
    return filepath

def run_asymptotic_analysis():
    n = 10000
    # Start Delta at a meaningful scale where log log delta flexes properly
    deltas = [16, 32, 64, 128, 256, 512, 1024]
    sims_per_delta = 5
    results = []
    
    print(f"Starting Robust Asymptotic Analysis: n = {n}")
    for delta in deltas:
        print(f"Testing Δ = {delta}...")
        filepath = generate_regular_test_graph(n, delta, f"graph_reg_d{delta}.txt")
        
        iteration_counts = []
        for i in range(sims_per_delta):
            algorithm = mis.GreedyMISInit(filepath, seed=None)
            supervisor = Supervisor(algorithm)
            supervisor.run_simulation()
            
            metrics = supervisor.phase_metrics
            phase_1_iters = metrics.get("PHASE_1_CHUNK_BROADCAST", 0)
            iteration_counts.append(phase_1_iters)
            
        avg_iters = sum(iteration_counts) / len(iteration_counts)
        
        results.append({
            "Delta": delta,
            "Avg_Phase_1_Iterations": avg_iters,
            "Min_Iterations": min(iteration_counts),
            "Max_Iterations": max(iteration_counts)
        })
        
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv("output/asymptotic_bounds.csv", index=False)
    print("\nData saved to output/asymptotic_bounds.csv")
    
    return df

def plot_results(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    deltas = df['Delta']
    y = df['Avg_Phase_1_Iterations']

    # Transform X to log(log(Delta)) space
    X_transformed = np.array([math.log2(math.log2(max(d, 2))) for d in deltas])

    ax.plot(X_transformed, y, marker='o', linestyle='-', color='#2e9e46', linewidth=3, 
            label='Empirical Phase 1 Iterations')
    ax.fill_between(X_transformed, df['Min_Iterations'], df['Max_Iterations'], color='#2e9e46', alpha=0.2, label='Spread')

    # Fit a direct linear model in log-log space to find the empirical slope (scaling exponent)
    k, b = np.polyfit(X_transformed, y, 1)
    fitted_y = k * X_transformed + b

    ax.plot(X_transformed, fitted_y, linestyle='--', color='#c0392b', linewidth=2, 
            label=f'Empirical Model: $y = {k:.2f} \\cdot \\log\\log \\Delta + {b:.2f}$')

    ax.set_title('Robust Asymptotic Verification via Regular Graph Topologies ($n = 10000$)', fontsize=14, pad=15)
    ax.set_xlabel('Theoretical Complexity Domain [$\log_2(\log_2 \Delta)$]', fontsize=12)
    ax.set_ylabel('Phase 1 Iterations ($i$)', fontsize=12)
    
    ax.set_xticks(X_transformed)
    ax.set_xticklabels([f"Δ={d}" for d in deltas])
    
    ax.legend(fontsize=11, loc='upper left')
    plt.tight_layout()
    
    os.makedirs("output", exist_ok=True)
    plot_path = "output/asymptotic_plot.png"
    plt.savefig(plot_path, dpi=300)
    print(f"Plot saved to {plot_path}")
    plt.show()

if __name__ == "__main__":
    data = run_asymptotic_analysis()
    plot_results(data)