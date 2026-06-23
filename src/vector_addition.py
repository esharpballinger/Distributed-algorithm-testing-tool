"""
File: vector_addition.py
Description: an implementation of a vector addition algorithm built to test the congested clique
             algorithm simulator
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

import random
from src.node import Node
from src.message import Message


def vector_addition_self_work(node):
    if node.inbox:
        node.data = sum(m.payload for m in node.inbox)
        node.inbox.clear()

def vector_addition_send_message(node, supervisor):
    for i in range(len(node.data)):
        supervisor.queue_message(Message(node.id, i, node.data[i]))

class VectorAddition:
    def __init__(self, n=None, seed=None):
        self.n = n if n is not None else int(input("Enter number of nodes in congested clique, n: "))
        self.seed = seed if seed is not None else random.randrange(2**32)
        random.seed(self.seed)

        self.vectors = []

        for _ in range(self.n):
            vector = []
            for _ in range(self.n):
                vector.append(random.randint(0, 100))
            self.vectors.append(vector)

        self.nodes = []
        for index in range(self.n):
            self.nodes.append(Node(vector_addition_self_work, vector_addition_send_message, self.vectors[index], id=index))

        self.expected_sum = [sum(vector[i] for vector in self.vectors) for i in range(len(self.vectors))]

    def is_goal_met(self, nodes) -> bool:
        return all(node.data == self.expected_sum[node.id] for node in nodes)


