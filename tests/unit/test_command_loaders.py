import unittest
from pathlib import Path
from unittest.mock import Mock

from harness.domain.message import Message
from harness.loader.command_context_loader import get_command_message_obj
from harness.loader.command_loader import CommandLoader


class CommandLoaderTests(unittest.TestCase):
    def test_parse_sections_preserves_boundaries_and_empty_sections(self):
        content = """Ignored preamble
# Name
example
# Empty
# Description
Example description
# Steps
First line

   
Second line
"""

        sections = CommandLoader()._parse_sections(content)

        self.assertEqual(
            sections,
            {
                "Name": "example",
                "Empty": "",
                "Description": "Example description",
                "Steps": "First line\nSecond line",
            },
        )

    def test_get_command_message_obj_reads_through_tool_registry(self):
        command_path = Path("/project/.caisa/commands/example.md")
        command_resolver = Mock()
        command_resolver.resolve.return_value = command_path
        tool_registry = Mock()
        tool_registry.execute.return_value = (
            "# Name\nexample\n# Description\nExample description"
        )

        message = get_command_message_obj(
            "example",
            command_resolver=command_resolver,
            tool_registry=tool_registry,
            command_loader=CommandLoader(),
        )

        tool_registry.execute.assert_called_once_with(
            "read_file",
            {"path": str(command_path)},
        )
        self.assertEqual(
            message,
            Message(
                role="system",
                content=(
                    "Executing command: example\n\n"
                    "Description:\nExample description"
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
