import os

from openai import OpenAI


class OpenAIClient:
    def __init__(self) -> None:
        self._client = OpenAI()
        self._model = os.getenv("OPENAI_MODEL", "gpt-5.5")

    def generate(self, message: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=message,
        )

        return response.output_text