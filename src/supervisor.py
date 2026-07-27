"""
File: supervisor.py
Description: entity which queues messages to send next round, runs a single round, and runs the simulation
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

from src.node import Node
from src.message import Message
from src.node import Algorithm
class Supervisor:

    def __init__(self, algorithm: Algorithm) -> None:
        self.algorithm = algorithm
        self.nodes = self.algorithm.nodes

        self.round = 0
        self.messages_sent_in_round = 0
        self.messages_queue = []
        self.phase_metrics = {}

    def reset(self):
        self.algorithm.__init__(None)
        self.nodes = self.algorithm.nodes

        self.round = 0
        self.messages_sent_in_round = 0
        self.messages_queue.clear()
        self.phase_metrics.clear()

    def queue_message(self, message: Message) -> None:
        self.messages_queue.append(message)

    def run_round(self) -> None:
        self.messages_queue = []

        #send message phase
        for node in self.nodes:
            node.send_message(self)

        #receive messages phase
        for message in self.messages_queue:
            recipient = self.nodes[message.receiver]
            recipient.receive_message(message)

        #computing phase
        for node in self.nodes:
            node.do_work()

        #a round passes
        self.round += 1
        self.messages_sent_in_round = (len(self.messages_queue))

    def run_simulation(self) -> int:
        while not self.algorithm.is_goal_met(self.nodes):
            current_phase = self.nodes[0].phase.name
            self.phase_metrics[current_phase] = self.phase_metrics.get(current_phase, 0) + 1
            self.run_round()
        return self.round