from harness.application.request.model.request import Request
from harness.domain.messages.message.model import Message
from harness.domain.sessions.session.model import Session
from harness.intelligence.models.contracts.model.contract import ModelClient


class Runner:
    def __init__(self, model_client: ModelClient) -> None:
        self._model_client = model_client
        self._session = Session()

    def handle(self, request: Request) -> str:
        if not request.message.strip():
            return "Please enter a message."

        user_message = Message(
            role="user",
            content=request.message,
        )

        self._session.add_message(user_message)

        response_text = self._model_client.generate(
            self._session.messages
        )

        assistant_message = Message(
            role="assistant",
            content=response_text,
        )

        self._session.add_message(assistant_message)

        return response_text