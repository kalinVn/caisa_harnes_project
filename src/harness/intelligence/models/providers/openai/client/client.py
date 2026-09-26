import os

from openai import OpenAI

from harness.domain.messages.message.model import Message
from harness.intelligence.models.contracts.response.model import ModelResponse
from harness.intelligence.models.parsing.response.parser import parse_model_response
from harness.intelligence.models.providers.openai.mapping.mapper import (
    map_messages,
)


class OpenAIClient:
    def __init__(self) -> None:
        self._client = OpenAI()

        self._model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5",
        )

    def generate(
        self,
        messages: list[Message],
    ) -> ModelResponse:

        if not messages:
            raise ValueError(
                "Cannot generate response with empty conversation."
            )

        input_messages = map_messages(messages)

        response = self._client.responses.create(
            model=self._model,
            input=input_messages,
        )

        return parse_model_response(response.output_text)
