import pandas as pd
import numpy as np
from matplotlib.ticker import StrMethodFormatter
import matplotlib.pyplot as plt
import math
import os

def replot_clean_graph():
    data_path = "output/detailed_asymptotic_bounds.csv"
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}. Please ensure the path is correct.")
        return
        
    df = pd.read_csv(data_path)
    df = df.fillna(0)

    plt.style.use('seaborn-v0_8-darkgrid')
    # Increased figure size slightly to accommodate larger text
    fig, ax1 = plt.subplots(figsize=(14, 8))

    deltas = df['Delta']
    x_indices = np.arange(len(deltas))
    
    # Reverse-engineer 'n' from Delta since it wasn't saved in the aggregated CSV.
    # The generator formula was: clique_size = max(4, n^0.66), and Delta = clique_size - 1
    # So, n is approximately (Delta + 1)^(1/0.66)
    n_values = [100, 250, 500, 1000, 2000, 4000, 8000]

    
    # Add 'n' to the labels and scale text up
    x_labels = [f"n={n_val}\nΔ={int(d)}\n(log2log2={math.log2(math.log2(max(d, 2))):.2f})" 
                for n_val, d in zip(n_values, deltas)]
    
    width = 0.6
    
    # Enhanced error bar styling
    error_kwargs_1 = {
        'elinewidth': 2.5,
        'capthick': 2.5,
        'ecolor': 'black'
    }

    error_kwargs_2 = {
            'elinewidth': 2.5,
            'capthick': 2.5,
            'ecolor': 'gray'
        }

    error_kwargs_3 = {
            'elinewidth': 2.5,
            'capthick': 2.5,
            'ecolor': 'green'
        }
    
    p1 = ax1.bar(x_indices, df['Phase_1_Rounds_mean'], width, 
                 yerr=df['Phase_1_Rounds_std'], capsize=6, error_kw=error_kwargs_1,
                 label='Phase 1: Subgraph Gather', color='#3498db', edgecolor='black')
                 
    p2 = ax1.bar(x_indices, df['Phase_2_Rounds_mean'], width, 
                 bottom=df['Phase_1_Rounds_mean'], 
                 yerr=df['Phase_2_Rounds_std'], capsize=6, error_kw=error_kwargs_2,
                 label='Phase 2: Dynamic Probability', color='#e67e22', edgecolor='black')
                 
    p3 = ax1.bar(x_indices, df['Phase_3_Rounds_mean'], width, 
                 bottom=df['Phase_1_Rounds_mean'] + df['Phase_2_Rounds_mean'], 
                 yerr=df['Phase_3_Rounds_std'], capsize=6, error_kw=error_kwargs_3,
                 label='Phase 3: Sparse Cleanup', color='#2ecc71', edgecolor='black')

    # SCALED UP TEXT SIZES
    ax1.set_xlabel('Graph Size & Maximum Degree Scaling', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Average Rounds per Phase', fontsize=16, fontweight='bold')
    ax1.set_title(r'MIS Phase Time across increasing $\Delta$ Congested Trap graphs', fontsize=18, fontweight='bold', pad=20)
    
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(x_labels, fontsize=13)
    ax1.tick_params(axis='y', labelsize=13)

    
    if 'Total_Messages_mean' in df.columns:
        ax2 = ax1.twinx()
        
        # Safely extract standard deviation for messages if it exists, otherwise default to 0
        msg_std = df['Total_Messages_std'] if 'Total_Messages_std' in df.columns else [0] * len(deltas)
        
        # Swapped ax2.plot for ax2.errorbar to support message variance
        ax2.errorbar(x_indices, df['Total_Messages_mean'], yerr=msg_std, color='#e74c3c', marker='D', 
                 linestyle='-', linewidth=3, capsize=6, elinewidth=2.5, capthick=2.5, ecolor='#c0392b', 
                 label='Total Network Messages', markersize=8)
                 
        ax2.set_ylabel('Total Messages Passed', color='#e74c3c', fontsize=16, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#e74c3c', labelsize=13)
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=14)
        ax2.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    else:
        ax1.legend(loc='upper left', fontsize=14)
    
    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plot_path = "output/detailed_phase_analysis_clean.png"
    plt.savefig(plot_path, dpi=300)
    print(f"Plot saved successfully to {plot_path}")
    plt.show()

if __name__ == "__main__":
    replot_clean_graph()