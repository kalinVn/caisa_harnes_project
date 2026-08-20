from harness.domain.messages.message.model import Message


def map_messages(
    messages: list[Message],
) -> list[dict[str, str]]:

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]