import os

from google import genai
from google.genai import types

from harness.domain.messages.message.model import Message
from harness.intelligence.models.providers.google.mapping.mapper import (
    map_messages,
)


class GeminiClient:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY"
            )

        self._client = genai.Client(
            api_key=api_key
        )

        self._model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

    def generate(
        self,
        messages: list[Message],
    ) -> str:

        contents, system_instruction = map_messages(
            messages
        )

        if not contents:
            raise ValueError(
                "Cannot generate response with empty conversation."
            )

        config = None

        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

        return response.text or ""