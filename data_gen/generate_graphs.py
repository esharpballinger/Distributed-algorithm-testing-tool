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
    Zero cycles means infinite girth, testing the 'tree local-view' limit.
    """
    adj = {i: set() for i in range(n)}
    for i in range(1, n):
        parent = (i - 1) // branching_factor
        adj[i].add(parent)
        adj[parent].add(i)
    return adj

def generate_scale_free(n, m=2):
    """
    Generates a scale-free graph using the Barabási-Albert preferential attachment model.
    Tests Phase 1 chunking threshold calculations by skewing delta.
    """
    adj = {i: set() for i in range(n)}
    
    # Initialize a small clique of size m+1
    for i in range(m + 1):
        for j in range(m + 1):
            if i != j:
                adj[i].add(j)
                
    # Track degrees for preferential attachment
    # A node's ID appears in this list a number of times equal to its degree
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

def generate_kmw_trap(n):
    """
    Generates a highly symmetric, bipartite-like graph.
    Creates a small dense core and a massive periphery, forming symmetric 4-cycles
    designed to cause constant marking collisions in Ghaffari's algorithm.
    """
    adj = {i: set() for i in range(n)}
    
    # Square root core size creates an aggressive bottleneck
    core_size = max(2, int(math.sqrt(n)))
    
    # Connect periphery nodes to subsets of the core
    for i in range(core_size, n):
        # Force symmetric 4-cycles by connecting to a pair in the core
        t1, t2 = random.sample(range(core_size), 2)
        adj[i].add(t1)
        adj[t1].add(i)
        adj[i].add(t2)
        adj[t2].add(i)
        
    return adj

if __name__ == "__main__":
    n = 1000  # Target node count for stress-testing

    # Generate a pure tree (High Girth)
    tree_adj = generate_balanced_tree(n, branching_factor=3)
    export_graph(n, tree_adj, "graph_tree_1000.txt")

    # Generate a Power-Law network (Scale-Free)
    scale_free_adj = generate_scale_free(n, m=3)
    export_graph(n, scale_free_adj, "graph_scale_free_1000.txt")

    # Generate a Symmetric Bipartite Trap (KMW-Style)
    kmw_adj = generate_kmw_trap(n)
    export_graph(n, kmw_adj, "graph_kmw_1000.txt")