from harness.domain.message import Message
from harness.models.response_instruction import MODEL_RESPONSE_INSTRUCTION


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
