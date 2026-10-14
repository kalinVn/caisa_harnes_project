import unittest

from harness.domain.message import Message
from harness.domain.tool_result import ToolResult


class MessageTest(unittest.TestCase):
    def test_has_tool_results(self):
        without_results = Message(role="user", content="No results")
        with_results = Message(
            role="user",
            content="Stored result",
            tool_results=(ToolResult("read_file", "output", id="result-id"),),
        )

        self.assertFalse(without_results.has_tool_results())
        self.assertTrue(with_results.has_tool_results())

    def test_has_requested_tool_results(self):
        message = Message(
            role="user",
            content="Stored results",
            tool_results=(
                ToolResult("read_file", "first output", id="first-id"),
                ToolResult("bash", "second output", id="second-id"),
            ),
        )

        self.assertTrue(message.has_requested_tool_results(["second-id"]))
        self.assertFalse(message.has_requested_tool_results(["unknown-id"]))
        self.assertFalse(message.has_requested_tool_results([]))


if __name__ == "__main__":
    unittest.main()
