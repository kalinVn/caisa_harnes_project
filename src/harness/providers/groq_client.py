import os

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from harness.domain.message import Message
from harness.mappers.groq_mapper import map_messages, map_response
from harness.models.errors import ModelConnectionError, ModelRateLimitError
from harness.models.response import ModelResponse


class GroqClient:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY")
        self._model = os.getenv("GROQ_MODEL", "").strip()
        if not self._model:
            raise ValueError("Missing GROQ_MODEL")
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=60.0,
            max_retries=2,
        )

    def generate(self, messages: list[Message]) -> ModelResponse:
        if not messages or not any(message.role != "system" for message in messages):
            raise ValueError("Cannot generate response with empty conversation.")
        mapped, tools = map_messages(messages)
        options = {"tools": tools, "tool_choice": "auto"} if tools else {
            "response_format": {"type": "json_object"},
        }
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=mapped,
                **options,
            )
        except RateLimitError as error:
            raise ModelRateLimitError("Groq request quota exceeded. Retry after the cooldown.") from error
        except APIConnectionError as error:
            raise ModelConnectionError("Groq could not be reached. Check the connection.") from error
        except APIStatusError as error:
            raise ModelConnectionError(
                f"Groq request failed ({error.status_code}). "
                "Check GROQ_API_KEY, GROQ_MODEL, and the model's tool support."
            ) from error
        if not response.choices:
            raise ValueError("Groq returned no response choices")
        choice = response.choices[0]
        if choice.finish_reason not in {"stop", "tool_calls"}:
            raise ValueError(f"Groq returned an incomplete response: {choice.finish_reason}")
        try:
            return map_response(choice.message, tools)
        except ValueError as error:
            raise ValueError(f"Groq returned an invalid model response: {error}") from error
