from dataclasses import dataclass, field
from uuid import uuid4

from harness.app.domain.message import Message


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid4()))
    messages: list[Message] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        self.messages.append(message)