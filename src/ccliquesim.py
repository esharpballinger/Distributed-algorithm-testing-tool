"""
File: ccliquesim.py
Description: Top level of Congested Clique simulation tool
Author: Evan Sharp-Ballinger
"""
import pandas as pd
from supervisor import *
from node import *

class CCTest:
    def __init__(self, algorithm, sim_count, input_file, output_file):
        supervisor = Supervisor(Algorithm())
