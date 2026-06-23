"""
File: message.py
Description: defines the structure of a message
Author: Evan Sharp-Ballinger & Gonzalo Estrella
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    sender: int
    receiver: int
    payload: Any