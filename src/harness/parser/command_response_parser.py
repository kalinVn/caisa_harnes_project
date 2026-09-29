import json


def parse_command_response(
    response_text: str,
) -> tuple[str, str]:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Command response did not follow the required "
            "JSON format."
        ) from error

    if not isinstance(payload, dict):
        raise ValueError(
            "Command response must be a JSON object."
        )

    answer = payload.get("answer")
    summary = payload.get("command_summary")

    if not isinstance(answer, str):
        raise ValueError(
            "Command response is missing a string answer."
        )

    if not isinstance(summary, str) or not summary.strip():
        raise ValueError(
            "Command response is missing a command summary."
        )

    return answer, summary.strip()
