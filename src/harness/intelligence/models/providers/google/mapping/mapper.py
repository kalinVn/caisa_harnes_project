from google.genai import types

from harness.domain.messages.message.model import Message


def map_messages(
    messages: list[Message],
) -> tuple[list[types.Content], str | None]:

    contents: list[types.Content] = []
    system_messages: list[str] = []

    for message in messages:
        if message.role == "system":
            system_messages.append(message.content)
            continue

        role = (
            "model"
            if message.role == "assistant"
            else "user"
        )

        contents.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(
                        text=message.content
                    )
                ],
            )
        )

    system_instruction = None

    if system_messages:
        system_instruction = "\n\n".join(
            system_messages
        )

    return contents, system_instruction