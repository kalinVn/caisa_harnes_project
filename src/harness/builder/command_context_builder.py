from harness.domain.command import Command


def build_command_context(command: Command) -> str:
    parts = [
        f"Executing command: {command.name}",
        f"Description:\n{command.description}",
    ]

    for section_name, section_content in command.sections.items():
        parts.append(
            f"{section_name}:\n"
            f"{section_content}"
        )

    return "\n\n".join(parts)
