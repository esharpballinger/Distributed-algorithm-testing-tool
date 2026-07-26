"""
File: ccliquesim.py
Description: Top level of Congested Clique simulation tool
Author: Evan Sharp-Ballinger
"""
import pandas as pd
from supervisor import *
from node import *

class CCSim:
    def __init__(self, algorithm, sim_count, input_file, output_file):
        self.supervisor = Supervisor(algorithm(input_file))
        self.output_file = output_file
        self.sim_count = sim_count

    def run_sims(self):
        round_output = []
        for i in range(self.sim_count):
            round_output.append(self.supervisor.run_simulation())
        round_output = pd.DataFrame(round_output, columns=['rounds'])
        round_output.to_csv(self.output_file)
