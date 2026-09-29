from dataclasses import dataclass


COMMAND_PREFIX = "execute command"


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    arguments: list[str]


def parse_command(text: str) -> ParsedCommand | None:
    normalized = text.strip()

    if not normalized.lower().startswith(COMMAND_PREFIX):
        return None

    remaining = normalized[len(COMMAND_PREFIX):].strip()

    if not remaining:
        raise ValueError("Command name is missing.")

    parts = remaining.split()

    return ParsedCommand(
        name=parts[0],
        arguments=parts[1:],
    )