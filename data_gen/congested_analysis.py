import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import concurrent.futures
from src import maximal_independent_set as mis
from src.supervisor import Supervisor
from generate_congested_graphs import generate_congestion_trap, export_graph
from graph_regenerate import replot_clean_graph

def run_single_simulation(filepath, n, delta):
    """
    Worker function to run a single simulation. 
    Instantiating the algorithm and supervisor inside the worker 
    ensures thread/process safety and avoids pickling issues.
    """
    algorithm = mis.GreedyMISInit(filepath, seed=None)
    supervisor = Supervisor(algorithm)
    
    total_rounds = supervisor.run_simulation()
    metrics = supervisor.phase_metrics
    
    phase_1_rounds = sum(v for k, v in metrics.items() if "PHASE_1" in k)
    phase_2_rounds = sum(v for k, v in metrics.items() if "PHASE_2" in k)
    phase_3_rounds = sum(v for k, v in metrics.items() if "PHASE_3" in k)
    
    total_messages = getattr(supervisor, 'total_messages_sent', 0) 
    
    return {
        "n": n,
        "Delta": delta,
        "Total_Rounds": total_rounds,
        "Phase_1_Rounds": phase_1_rounds,
        "Phase_2_Rounds": phase_2_rounds,
        "Phase_3_Rounds": phase_3_rounds,
        "Total_Messages": total_messages
    }

def run_detailed_complexity_analysis():
    n_values = [100, 250, 500, 1000, 2000, 4000, 8000]
    sims_per_graph = 400
    
    print("Generating Congestion Traps...")
    
    # 1. Generate all graphs serially first and prepare the task list
    tasks = []
    for n in n_values:
        adj = generate_congestion_trap(n)
        filename = f"graph_congestion_{n}.txt"
        export_graph(n, adj, filename)
        
        delta = max(len(neighbors) for neighbors in adj.values())
        filepath = f"src/{filename}"
        
        # Queue up the simulation arguments
        for _ in range(sims_per_graph):
            tasks.append((filepath, n, delta))
            
    print(f"Queued {len(tasks)} total simulations. Starting parallel execution...")
    
    # 2. Run simulations concurrently using all available CPU cores
    results = []
    # ProcessPoolExecutor bypasses the GIL for true CPU parallelism
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Map the worker function to our tasks
        futures = [executor.submit(run_single_simulation, *task) for task in tasks]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            # Print a progress update every 10% of completion
            if i % max(1, (len(tasks) // 10)) == 0:
                print(f"Progress: {i}/{len(tasks)} simulations completed.")
                
    print("All simulations finished successfully.")
            
    # 3. Aggregate and save the data
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(results)
    
    agg_df = df.groupby('Delta').agg({
        'Phase_1_Rounds': ['mean', 'std'],
        'Phase_2_Rounds': ['mean', 'std'],
        'Phase_3_Rounds': ['mean', 'std'],
        'Total_Messages': ['mean', 'std']
    }).reset_index()
    
    agg_df.columns = ['_'.join(col).strip('_') for col in agg_df.columns.values]
    
    agg_df.to_csv("output/detailed_asymptotic_bounds.csv", index=False)
    print("\nData saved to output/detailed_asymptotic_bounds.csv")
    
    return agg_df

def plot_phase_breakdown(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax1 = plt.subplots(figsize=(12, 7))

    deltas = df['Delta']
    x_transformed = np.array([math.log2(math.log2(max(d, 2))) for d in deltas])
    
    width = 0.35
    
    p1 = ax1.bar(x_transformed, df['Phase_1_Rounds_mean'], width, 
                 yerr=df['Phase_1_Rounds_std'], capsize=5, 
                 label='Phase 1: Subgraph Gather', color='#3498db', edgecolor='black')
                 
    p2 = ax1.bar(x_transformed, df['Phase_2_Rounds_mean'], width, 
                 bottom=df['Phase_1_Rounds_mean'], 
                 yerr=df['Phase_2_Rounds_std'], capsize=5, 
                 label='Phase 2: Dynamic Probability', color='#e67e22', edgecolor='black')
                 
    p3 = ax1.bar(x_transformed, df['Phase_3_Rounds_mean'], width, 
                 bottom=df['Phase_1_Rounds_mean'] + df['Phase_2_Rounds_mean'], 
                 yerr=df['Phase_3_Rounds_std'], capsize=5, 
                 label='Phase 3: Sparse Cleanup', color='#2ecc71', edgecolor='black')

    ax1.set_xlabel('$\log_2(\log_2 \Delta)$', fontsize=12)
    ax1.set_ylabel('Average Rounds per Phase', fontsize=12)
    ax1.set_title('MIS Phase Breakdown & Message Complexity (N=50)', fontsize=14, pad=15)
    
    ax1.set_xticks(x_transformed)
    ax1.set_xticklabels([f"$\Delta$={int(d)}" for d in deltas])
    
    if 'Total_Messages_mean' in df.columns and df['Total_Messages_mean'].sum() > 0:
        ax2 = ax1.twinx()
        ax2.plot(x_transformed, df['Total_Messages_mean'], color='#e74c3c', marker='D', 
                 linestyle='-', linewidth=2, label='Total Network Messages')
        ax2.set_ylabel('Total Messages Passed', color='#e74c3c', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='#e74c3c')
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')
    else:
        ax1.legend(loc='upper left')

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plot_path = "output/detailed_phase_analysis.png"
    plt.savefig(plot_path, dpi=300)
    print(f"Plot saved to {plot_path}")
    plt.show()

if __name__ == "__main__":
    data = run_detailed_complexity_analysis()
    replot_clean_graph()