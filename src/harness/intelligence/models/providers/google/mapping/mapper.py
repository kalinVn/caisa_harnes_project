from google.genai import types

from harness.domain.messages.message.model import Message


TOOL_CALL_INSTRUCTION = """
When you need to use a tool, respond only with valid JSON.

Use exactly this format:

{
  "tool": "<tool_name>",
  "arguments": {
    "<argument_name>": "<argument_value>"
  }
}

Do not wrap the JSON in Markdown code fences.
Do not include explanatory text before or after the JSON.

If no tool is required, respond normally with text.
""".strip()


def map_messages(
    messages: list[Message],
) -> tuple[list[types.Content], str | None]:
    contents: list[types.Content] = []
    system_messages: list[str] = []

    for message in messages:
        if message.role == "system":
            system_messages.append(
                message.content
            )
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

    system_messages.append(
        TOOL_CALL_INSTRUCTION
    )

    system_instruction = "\n\n".join(
        system_messages
    )

    return contents, system_instruction