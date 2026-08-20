from typing import Protocol


class ModelClient(Protocol):
    def generate(self, message: str) -> str:
        ...