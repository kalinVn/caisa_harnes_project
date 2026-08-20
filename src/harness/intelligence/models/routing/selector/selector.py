import os

from harness.intelligence.models.providers.openai.client.client import OpenAIClient
from harness.intelligence.models.providers.google.client.client import GeminiClient


def create_model_client():
    provider = os.getenv("MODEL_PROVIDER", "google").lower()

    if provider == "openai":
        return OpenAIClient()

    if provider in {"google", "gemini"}:
        return GeminiClient()

    raise ValueError(
        f"Unsupported MODEL_PROVIDER: {provider}"
    )