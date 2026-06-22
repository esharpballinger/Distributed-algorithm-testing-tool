from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    sender: int
    receiver: int
    payload: Any