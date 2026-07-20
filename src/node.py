"""
File: node.py
Description: defines the structure of a single node in a graph
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

class Node:

    def __init__(self, self_work, send_message, data, id=None) -> None:
        """
        Initialize self work function and the data
        :param self_work: A function pointer to the work that the node can do between rounds for free
        :param send_message: A function pointer to send a message to another node
        :param data: The data that the node has access to
        :param id: The id of the node
        """
        self.self_work = self_work
        self.send_message = send_message
        self.data = data  #a bunch hof relations, for a VA it is going to be just one vector
        self.id = id
        self.inbox =[]

    def receive_message(self, message, sender) -> None:
        """
        Receive message from another node and store it in the inbox
        :param message: The received message
        :param sender: the node that sent the message
        """
        self.inbox.append(message)

    def do_work(self) -> None:
        """
        Does work for "free" using the function pointer contained in the node
        """
        self.self_work(self)
