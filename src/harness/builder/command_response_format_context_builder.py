from harness.domain.message import Message


def build_command_response_format_context() -> Message:
    return Message(
        role="system",
        content=(
            "When this command is complete and no more tools "
            "are needed, put a JSON-encoded object in the `text` string "
            "of the standard model response envelope. This inner object has "
            "exactly two string fields: `answer`, containing the "
            "normal user-facing response, and "
            "`command_summary`, containing one concise semantic "
            "sentence for durable history. Do not wrap the JSON "
            "in Markdown. Keep the outer `text`, `tool_calls`, and "
            "`tool_result_summaries` fields, including any summaries due. "
            "Do not include raw logs, file contents, "
            "or command instructions in `command_summary`. This "
            "format applies only to the final response; tool-call "
            "responses must continue to use the tool protocol."
        ),
    )
