from harness.domain.command import Command

# Взима създадения Command обект с полетата name, description и sections.
# Изгражда от тях текстов контекст, който се подава към LLM модела.
#
# Пример за входен Command обект:
# name = "write_file"
# description = "Creates a new file"
# sections = {"Usage": "write_file path content"}
#
# Резултатът е един форматиран текст:
# Name: write_file
# Description: Creates a new file
# Usage: write_file path content

def create_context_from_command_obj(command_obj: Command) -> str:
    parts = [
        f"Executing command: {command_obj.name}",
        f"Description:\n{command_obj.description}",
    ]

    for section_name, section_content in command_obj.sections.items():
        parts.append(
            f"{section_name}:\n"
            f"{section_content}"
        )

    return "\n\n".join(parts)
