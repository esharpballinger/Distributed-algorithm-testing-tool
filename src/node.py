class Node:

    self_work: function = None
    work_after_receiving: function = None
    data: any = None
    id: int = None

    def __init__(self, self_work, data, receiving_func) -> None:
        """
        Initialize self work function and the data
        :param self_work: A function pointer to the work that the node can do between rounds for free
        :param data: The data that the node has access to
        """
        self.self_work = self_work
        self.data = data
        self.work_after_receiving = receiving_func
    
    def send_message(self, message, recipient: Node) -> None:
        """
        Sends a message to a recipient node
        :param message: the message to send
        :param recipient: The recipient node
        """
        recipient.receive_message(message, self)

    def receive_message(self, message, sender) -> None:
        """
        Recieve message from another node
        :param message: The recieved message
        :param sender: the node that sent the message
        """
        self.work_after_receiving(self, message)
        pass

    def do_work(self) -> None:
        """
        Does work for "free" using the function pointer contained in the node
        """
        self.self_work(self)

    def change_data(self, new_data):
        self.data = new_data
        return self.data
