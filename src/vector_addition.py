"""
File: vector_addition.py
Description: an implementation of a vector addition algorithm built to test the congested clique
             algorithm simulator
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

import random
from src.node import Node
from src.message import Message
from src.node import Algorithm

class VectorAddition(Node):
    def do_work(self):
        if self.inbox:
            self.data = sum(m.payload for m in self.inbox)
            self.inbox.clear()

    def send_message(self, supervisor):
        for i in range(len(self.data)):
            supervisor.queue_message(Message(self.id, i, self.data[i]))

class VectorAdditionInit(Algorithm):
    def __init__(self, n=None, seed=None):
        self.n = n if n is not None else int(input("Enter number of nodes in congested clique, n: "))
        self.seed = seed if seed is not None else random.randrange(2**32)
        random.seed(self.seed)

        self.vectors = [[random.randint(0,100) for _ in range(self.n)] for _ in range(self.n)]

        self.nodes = []
        for index in range(self.n):
            self.nodes.append(VectorAddition(self.vectors[index], id=index))

        self.expected_sum = [sum(vector[i] for vector in self.vectors) for i in range(len(self.vectors))]

    def is_goal_met(self, nodes) -> bool:
        return all(node.data == self.expected_sum[node.id] for node in nodes)


