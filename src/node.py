"""
File: node.py
Description: defines the structure of a single node in a graph
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

from abc import ABC, abstractmethod
class Node(ABC):
    def __init__(self, data, id=None) -> None:
        """
        Initialize self work function and the data
        :param self_work: A function pointer to the work that the node can do between rounds for free
        :param send_message: A function pointer to send a message to another node
        :param data: The data that the node has access to
        :param id: The id of the node
        """
        self.data = data  
        self.id = id
        self.inbox =[]

    def receive_message(self, message) -> None:
        """
        Receive message from another node and store it in the inbox
        :param message: The received message
        :param sender: the node that sent the message
        """
        self.inbox.append(message)

    @abstractmethod
    def send_message(self, supervisor) -> None:
        """
        Sends message to another node (via the supervisor)
        :param message: the message to send
        :param recipient: the node to send the message to
        """
        pass

    @abstractmethod
    def do_work(self) -> None:
        """
        Does work for "free" 
        """
        pass


class Algorithm(ABC):
    """
    Abstract class that represents the overarching class for an algorithm
    Responsible for initializing nodes and determining if the algorithm is finished running
    """
    @abstractmethod
    def __init__(self, input_filename):
        """
        builds the list of nodes for the algorithm
        :param input_filename: file describing the input (e.g. a graph)
        """

    @abstractmethod
    def is_goal_met(self, nodes):
        """
        determines if the algorithm is done running
        :param nodes: The list of nodes
        """

    @staticmethod
    def graph_input(filename) -> dict:
        """
        format for input files:
        integer at top shows how many lines in the file
        every line after has the neighbors of that node separated by spaces
        """
        with open(filename, "r") as f:
            n = int(f.readline().strip())
            graph = {i: [] for i in range(n)}
            for i, line in enumerate(f):
                graph[i] = [int(neighbor) for neighbor in line.strip().split()]
        
        return graph