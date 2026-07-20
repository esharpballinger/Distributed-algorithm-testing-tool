"""
File: supervisor.py
Description: entity which queues messages to send next round, runs a single round, and runs the simulation
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

from src.node import Node
from src.message import Message

class Supervisor:

    def __init__(self, nodes: list[Node], vector_addition) -> None:
        self.nodes = nodes
        self.vector_addition = vector_addition

        self.round = 0
        self.messages_sent_in_round = 0
        self.messages_queue = []

    def queue_message(self, message: Message) -> None:
        self.messages_queue.append(message)

    def run_round(self) -> None:
        self.messages_queue = []

        #send message phase
        for node in self.nodes:
            node.send_message(node, self)

        #receive messages phase
        for message in self.messages_queue:
            recipient = self.nodes[message.receiver]
            recipient.receive_message(message, message.sender)

        #computing phase
        for node in self.nodes:
            node.do_work()

        #a round passes
        self.round += 1
        self.messages_sent_in_round = (len(self.messages_queue))

    def run_simulation(self) -> bool:
        while not self.vector_addition.is_goal_met(self.nodes):
            self.run_round()
        return True