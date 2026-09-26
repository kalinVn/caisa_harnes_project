from harness.domain.messages.message.model import Message
from harness.intelligence.models.contracts.response.instruction import MODEL_RESPONSE_INSTRUCTION


def map_messages(
    messages: list[Message],
) -> list[dict[str, str]]:

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ] + [{"role": "system", "content": MODEL_RESPONSE_INSTRUCTION}]
