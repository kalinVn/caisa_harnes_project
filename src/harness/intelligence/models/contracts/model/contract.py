from typing import Protocol

from harness.domain.messages.message.model import Message
from harness.intelligence.models.contracts.response.model import (
    ModelResponse,
)


class ModelClient(Protocol):

    def generate(
        self,
        messages: list[Message],
    ) -> ModelResponse:
        ...