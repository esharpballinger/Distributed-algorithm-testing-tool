import random
from node import Node
from message import Message

class Supervisor:

    def __init__(self, nodes: list[Node], seed: int = None) -> None:
        if seed is None:
            self.seed = random.randrange(2**32)
        else:
            self.seed = seed
        self.nodes = nodes
        random.seed(self.seed)

        self.round = 0
        self.messages_sent_in_round = 0
        self.messages_queue = []

    def queue_message(self, message: Message) -> None:
        self.messages_queue.append(message)

    def run_round(self) -> None:
        if self.round == 0:
            initial_sends(self)
        else:
            self.messages_queue = []

        for node in self.nodes:
            node.do_work()

        for message in self.messages_queue:
            recipient = self.nodes[message.receiver]
            recipient.receive_message(message, message.sender)

        for node in self.nodes:
            for message in node.inbox:
                node.work_after_receiving(node, message)
            node.inbox = []

        self.round += 1
        self.messages_sent_in_round = (len(self.messages_queue))