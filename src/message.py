from dataclasses import dataclass

@dataclass
class Message:
    sender: int
    receiver: int
    payload: str