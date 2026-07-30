import sys
from src.maximal_independent_set import GreedyMISInit
import src.mis_visualization as viz

def main():
    input_file = "src/finalgraphs/graph_25.txt"
    output_html = "mis_visualization_output.html"
    
    print(f"Loading graph and initializing algorithm from '{input_file}'...")
    try:
        algorithm = GreedyMISInit(input_file)
    except FileNotFoundError:
        print(f"Error: Could not find '{input_file}'. Ensure it is in the same directory.")
        sys.exit(1)
    
    print("Running simulation... (this may take a few moments)")
    supervisor, history, messages = viz.run_with_history(algorithm)
    
    print("Rendering HTML...")
    viz.write_html(algorithm, history, messages, output_html)
    print(f"Success! Open '{output_html}' in your web browser to view the interactive visualization.")

if __name__ == "__main__":
    main()