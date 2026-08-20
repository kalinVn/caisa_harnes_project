from dataclasses import dataclass
from typing import Literal


MessageRole = Literal["user", "assistant", "system"]


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str