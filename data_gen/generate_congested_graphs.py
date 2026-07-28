import random
import math
from pathlib import Path

def export_graph(n, adj, filename):
    """Writes the adjacency list to the specified text file."""
    output_dir = Path("src")
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        f.write(f"{n}\n")
        for i in range(n):
            # Sort neighbors for deterministic, clean output
            neighbors = sorted(list(adj[i]))
            f.write(" ".join(map(str, neighbors)) + "\n")
    print(f"Generated {filepath} ({n} nodes, {sum(len(v) for v in adj.values()) // 2} edges)")

def generate_balanced_tree(n, branching_factor=2):
    """
    Generates a balanced k-ary tree.
    """
    adj = {i: set() for i in range(n)}
    for i in range(1, n):
        parent = (i - 1) // branching_factor
        adj[i].add(parent)
        adj[parent].add(i)
    return adj

def generate_scale_free(n, m=2):
    """
    Generates a scale-free graph using the Barabási-Albert model.
    """
    adj = {i: set() for i in range(n)}
    
    for i in range(m + 1):
        for j in range(m + 1):
            if i != j:
                adj[i].add(j)
                
    nodes_by_degree = list(range(m + 1)) * m 
    
    for i in range(m + 1, n):
        targets = set()
        while len(targets) < m:
            targets.add(random.choice(nodes_by_degree))
        
        for t in targets:
            adj[i].add(t)
            adj[t].add(i)
            nodes_by_degree.extend([i, t])
            
    return adj

def generate_congestion_trap(n):
    """
    Generates a graph designed specifically to stress-test Congested Clique bandwidth.
    Constructs a disjoint union of dense cliques. If the random permutation selects 
    many nodes from the same clique in an early chunk, the induced edges sent to the 
    leader node will surge, testing the O(n) edge bound of Phase 1.
    """
    adj = {i: set() for i in range(n)}
    
    # Create cliques of size roughly n^(2/3) to ensure high localized density
    clique_size = max(4, int(math.pow(n, 0.66)))
    
    current_node = 0
    while current_node < n:
        # Determine the size of the current clique (handle the remainder)
        current_clique_size = min(clique_size, n - current_node)
        
        # Fully connect all nodes within this specific clique
        clique_nodes = range(current_node, current_node + current_clique_size)
        for i in clique_nodes:
            for j in clique_nodes:
                if i != j:
                    adj[i].add(j)
                    
        current_node += current_clique_size
        
    return adj

if __name__ == "__main__":
    n = 1000  # Target node count for stress-testing

    # Generate a pure tree
    tree_adj = generate_balanced_tree(n, branching_factor=3)
    export_graph(n, tree_adj, "graph_tree_1000.txt")

    # Generate a Power-Law network 
    scale_free_adj = generate_scale_free(n, m=3)
    export_graph(n, scale_free_adj, "graph_scale_free_1000.txt")

    # Generate a Congestion Trap (Congested-Clique Stress Test)
    congestion_adj = generate_congestion_trap(n)
    export_graph(n, congestion_adj, "graph_congestion_1000.txt")