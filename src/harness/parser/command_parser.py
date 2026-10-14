from dataclasses import dataclass


COMMAND_PREFIX = "execute command"


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    arguments: list[str]


def parse_command(text: str) -> ParsedCommand | None:
    """Parse input text into a ParsedCommand with a name and arguments.

    Example input: "execute command read_file test.txt"
    Example output: ParsedCommand(name="read_file", arguments=["test.txt"])
    """

    # Normalize the input by removing leading and trailing whitespace.

    normalized_command_text = text.strip()


    # Return None unless the normalized text begins with COMMAND_PREFIX.
    if not normalized_command_text.lower().startswith(COMMAND_PREFIX):
        return None

    # Remove COMMAND_PREFIX and trim the remaining command text.
    command_name = normalized_command_text[len(COMMAND_PREFIX):].strip()

    if not command_name:
        raise ValueError("Command name is missing.")

    parts = command_name.split()

    # Store the command name and all remaining parts as arguments.
    # ParsedCommand only stores these values; it does not execute the command.
                                                                    
    return ParsedCommand(
        name=parts[0],
        arguments=parts[1:],
    )
