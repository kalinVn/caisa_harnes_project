import json


def parse_command_response(response_text: str) -> tuple[str, str] | None:
    """Parse a command reply, or return None if its expected JSON format is invalid."""
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    answer = payload.get("answer")
    summary = payload.get("command_summary")

    if not isinstance(answer, str):
        return None

    if not isinstance(summary, str) or not summary.strip():
        return None

    return answer, summary.strip()
