import os

from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        self._client = genai.Client(api_key=api_key)
        self._model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

    def generate(self, message: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=message,
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True,
                ),
            ),
        )

        return response.text or ""