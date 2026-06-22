"""
File: vector_addition.py
Description: an implementation of a vector addition algorithm built to test the congested clique
             algorithm simulator
             Anatomy of the "data" attribute of the node class for this algorithm:
                data[0]: The initial vector that the node has upon initialization
                data[1]: The components of the vectors sent from other nodes corresponding to the 
                         node's id
                data[2]: The computed sum
                data[3]: The final vector (empty on all except for vector 1)
Author: Evan Sharp-Ballinger
"""
import node
import random

def initialize_data(n, upper_limit) -> list:
    data = [[],[],None,[None]*n]
    for i in range(n):
        data[0].append(random.randint(-10**n-1, 10**n-1))
    return data

def receive_component(node: node.Node, message: int, sender: node.Node) -> None:
    node.data[1].append(message)
    # Looking to replace this with a queue based message processing system since self work is free


def add_components(node: node.Node) -> None:
    components: list = node.data[1]
    sum = sum(components)
    node.data[2] = sum
    return


if __name__ == "__main__":
    pass


