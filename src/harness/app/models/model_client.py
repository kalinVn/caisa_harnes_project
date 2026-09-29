from typing import Protocol

from harness.app.domain.message import Message
from harness.app.models.response import ModelResponse


class ModelClient(Protocol):

    def generate(
        self,
        messages: list[Message],
    ) -> ModelResponse:
        ...