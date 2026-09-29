import unittest
from unittest.mock import Mock, patch

from harness.app.orchestrator import Runner
from harness.app.session_manager import SessionManager
from harness.app.models.request import Request
from harness.app.domain.message import Message
from harness.app.domain.tool_call import ToolCall
from harness.app.domain.tool_result import ToolResult
from harness.app.models.response import ModelResponse
from harness.app.models.tool_result_summary import ToolResultSummary


class RunnerToolResultSummariesTest(unittest.TestCase):
    def test_applies_summaries_before_final_response_or_new_tool_execution(self):
        for has_tool_calls in (False, True):
            with self.subTest(has_tool_calls=has_tool_calls):
                result = ToolResult("read_file", "full original contents")
                untouched = ToolResult("read_file", "another full output")
                summary = "Contains the main orchestration loop."
                client = Mock()
                client.generate.side_effect = [
                    ModelResponse(
                        text="Done",
                        tool_calls=[ToolCall("read_file", {"path": "next.py"})] if has_tool_calls else [],
                        tool_result_summaries=[
                            ToolResultSummary(result.id, summary),
                            ToolResultSummary("unknown-id", "Ignore this summary."),
                        ],
                    ),
                    ModelResponse(text="Done"),
                ]
                with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
                    runner = Runner(client)
                session = runner._session_manager.current_session
                stored_message = Message(role="user", content=result.output, tool_results=(result, untouched))
                session.add_message(stored_message)

                def execute(name, arguments):
                    self.assertEqual(result.summary, summary)
                    return "new tool output"

                runner._tool_registry.execute = Mock(side_effect=execute)

                self.assertEqual(runner.handle(Request.create("Continue")), "Done")

                self.assertIs(session.messages[2], stored_message)
                self.assertIs(stored_message.tool_results[0], result)
                self.assertEqual(result.summary, summary)
                self.assertEqual(result.output, "full original contents")
                self.assertEqual(stored_message.content, "full original contents")
                self.assertEqual(untouched.summary, "")
                self.assertEqual(untouched.output, "another full output")
                stored_results = [item for message in session.messages for item in message.tool_results]
                self.assertEqual(len(stored_results), 3 if has_tool_calls else 2)
                self.assertEqual(client.generate.call_count, 2 if has_tool_calls else 1)
                if has_tool_calls:
                    runner._tool_registry.execute.assert_called_once_with("read_file", {"path": "next.py"})
                    next_messages = client.generate.call_args_list[1].args[0]
                    self.assertTrue(any(summary in message.content for message in next_messages))
                    self.assertFalse(any(result.output in message.content for message in next_messages))
                else:
                    runner._tool_registry.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
