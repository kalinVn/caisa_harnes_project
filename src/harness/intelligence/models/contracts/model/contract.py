from typing import Protocol

from harness.domain.messages.message.model import Message


class ModelClient(Protocol):
    def generate(self, messages: list[Message]) -> str:
        ...