import os

from harness.intelligence.models.contracts.model.contract import ModelClient
from harness.intelligence.models.providers.google.client.client import (
    GeminiClient,
)
from harness.intelligence.models.providers.openai.client.client import (
    OpenAIClient,
)


def create_model_client() -> ModelClient:
    provider = os.getenv(
        "MODEL_PROVIDER",
        "google",
    ).lower()

    if provider in {"google", "gemini"}:
        return GeminiClient()

    if provider == "openai":
        return OpenAIClient()

    raise ValueError(
        f"Unsupported MODEL_PROVIDER: {provider}"
    )