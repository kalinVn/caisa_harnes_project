from typing import Protocol

from harness.domain.message import Message
from harness.models.response import ModelResponse


class ModelClient(Protocol):

    def generate(
        self,
        messages: list[Message],
    ) -> ModelResponse:
        ...