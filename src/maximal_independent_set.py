"""
File: maximal_independent_set.py
Description: An implementation of the Maximal Independent Set Congested Clique algorithm for the congested clique simulator
Author: Evan Sharp-Ballinger and Gonzalo Estrella

Greedy randomized MIS (Ghaffari, Gouleakis, Konrad, Mitrovic, Rubinfeld,
arXiv:1802.08237, p.6): draw a random permutation pi of the vertices; a vertex
joins the MIS iff no earlier-ranked neighbor joined. Simulated here in
parallel rounds: each round every undecided node exchanges (status, rank)
with its still-active problem-graph neighbors and joins when it holds the
smallest rank among them. Output is identical to sequential greedy for the
same permutation. Communication stays congested-clique; nodes simply only
address their problem-graph neighbors.
"""

import random
from enum import Enum

from src.node import Node, Algorithm
from src.message import Message


class Status(Enum):
    UNDECIDED = "undecided"
    IN_MIS = "in_mis"
    OUT = "out"


class MISNode(Node):
    def __init__(self, rank, neighbors, id=None):
        super().__init__(Status.UNDECIDED, id=id)
        self.rank = rank
        self.neighbors = set(neighbors)
        self.active_neighbors = set(neighbors)
        self.announced_decision = False

    def send_message(self, supervisor):
        if self.data is not Status.UNDECIDED:
            if self.announced_decision:
                return
            self.announced_decision = True
        for neighbor in self.active_neighbors:
            supervisor.queue_message(Message(self.id, neighbor, (self.data, self.rank)))

    def do_work(self):
        if self.data is not Status.UNDECIDED:
            self.inbox.clear()
            return

        undecided_ranks = []
        for message in self.inbox:
            status, rank = message.payload
            if status is Status.UNDECIDED:
                undecided_ranks.append(rank)
            else:
                if status is Status.IN_MIS:
                    self.data = Status.OUT
                self.active_neighbors.discard(message.sender)
        self.inbox.clear()

        if self.data is Status.UNDECIDED and all(self.rank < r for r in undecided_ranks):
            self.data = Status.IN_MIS


class GreedyMISInit(Algorithm):
    def __init__(self, input_filename, seed=None):
        self.seed = seed if seed is not None else random.randrange(2**32)
        random.seed(self.seed)

        raw_graph = Algorithm.graph_input(input_filename)
        self.n = len(raw_graph)

        # undirected problem graph: symmetrize the file's adjacency lists and drop self-loops
        self.graph = {i: set() for i in range(self.n)}
        for u, neighbors in raw_graph.items():
            for v in neighbors:
                if u != v:
                    self.graph[u].add(v)
                    self.graph[v].add(u)

        # random permutation pi: ranks[v] is v's position in the greedy order
        self.ranks = random.sample(range(self.n), self.n)

        self.nodes = [
            MISNode(self.ranks[index], self.graph[index], id=index)
            for index in range(self.n)
        ]

        self.expected_mis = self._sequential_greedy_mis()

    def _sequential_greedy_mis(self):
        """Ground truth: the paper's sequential GreedyMIS over the same permutation."""
        mis = set()
        removed = set()
        for v in sorted(range(self.n), key=lambda v: self.ranks[v]):
            if v not in removed:
                mis.add(v)
                removed.update(self.graph[v])
        return mis

    def is_goal_met(self, nodes) -> bool:
        return all(node.data is not Status.UNDECIDED for node in nodes)
