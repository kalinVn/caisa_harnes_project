from harness.application.request.model.request import Request
from harness.intelligence.models.contracts.model.contract import ModelClient


class Runner:
    def __init__(self, model_client: ModelClient) -> None:
        self._model_client = model_client

    def handle(self, request: Request) -> str:
        return self._model_client.generate(request.message)