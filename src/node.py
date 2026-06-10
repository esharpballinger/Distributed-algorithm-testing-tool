class Node:

    self_work: function = None
    data = None

    def __init__(self, self_work, data):
        """
        Initialize self work function and the data
        :param self_work: A function pointer to the work that the node can do between rounds for free
        :param data: The data that the node has access to
        """
        pass
    
    def send_message(self, message, recipient: Node):
        """
        Sends a message to a recipient node
        :param message: the message to send
        :param recipient: The recipient node
        """
        recipient.receive_message(message, self)

    def receive_message(self, message, sender):
        """
        (Work in progress, there is likely a better way to do this)
        Recieve message from another node
        :param message: The recieved message
        :param sender: the node that sent the message
        """
        # Do some work, send a response, etc
        pass

    def do_work(self):
        """
        Does work for "free" using the function pointer contained in the node
        """
        # Will use the function pointer in some way
        pass
