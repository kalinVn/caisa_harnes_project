from dataclasses import dataclass


COMMAND_PREFIX = "execute command"


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    arguments: list[str]


def parse_command(text: str) -> ParsedCommand | None:
    """Parse input text into a command name and its arguments.

    Example input: "execute command read_file test.txt"
    Result: ParsedCommand(name="read_file", arguments=["test.txt"])
    """

    # Normalize input by removing leading and trailing whitespace.

    normalized_command_text = text.strip()


    # Continue only when normalized input starts with COMMAND_PREFIX.
    # For example, accept "execute command read_file text.txt" but return None
    # for "read_file text.txt".
    if not normalized_command_text.lower().startswith(COMMAND_PREFIX):
        return None

    # Remove COMMAND_PREFIX and trim the remaining text. For example,
    # "execute command read_file test.txt" becomes "read_file test.txt".
    command_name = normalized_command_text[len(COMMAND_PREFIX):].strip()

    if not command_name:
        raise ValueError("Command name is missing.")

    parts = command_name.split()

    # Create a ParsedCommand containing the command name and all arguments.
    # ParsedCommand only stores this data; it does not execute the command.

    # Example input: "execute command write_file test1.txt test2.txt test3.txt"
    # Result: name="write_file" and arguments=["test1.txt", "test2.txt", "test3.txt"].
                                                                    
    return ParsedCommand(
        name=parts[0],
        arguments=parts[1:],
    )
