from dataclasses import dataclass, field
from message import Message

@dataclass
class Machine:
    id: int
    name: str
    sends_answer: bool
    to_process: list[Message] = field(default_factory=list)
    #holds a relation

