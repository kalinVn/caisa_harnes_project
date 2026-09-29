import unittest
from copy import deepcopy
from unittest.mock import Mock, patch
from uuid import UUID

from harness.orchestrator import Runner
from harness.session_manager import SessionManager
from harness.models.request import Request
from harness.domain.message import Message
from harness.domain.tool_call import ToolCall
from harness.domain.tool_result import ToolResult
from harness.builder.model_message_builder import ModelMessageBuilder
from harness.models.response import ModelResponse


class ModelMessageBuilderTest(unittest.TestCase):
    def test_tool_results_generate_unique_ids_and_allow_summary_assignment(self):
        first = ToolResult("read_file", "contents")
        second = ToolResult("read_file", "contents")

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(UUID(first.id).version, 4)
        self.assertEqual(UUID(second.id).version, 4)
        first.summary = "Read configuration."
        self.assertEqual(first.summary, "Read configuration.")

    def test_build_preserves_history_and_replaces_only_tool_results(self):
        results = (
            ToolResult("read_file", "full file contents", "Read config.py successfully."),
            ToolResult("bash", "full error output", "bash failed.", success=False),
        )
        messages = [
            Message(role="system", content="Instructions"),
            Message(role="user", content="Read config.py"),
            Message(role="assistant", content="Reading config.py"),
            Message(role="user", content="full raw tool results", tool_results=results),
        ]
        original = deepcopy(messages)

        model_messages = ModelMessageBuilder().build(messages)

        self.assertIsNot(model_messages, messages)
        self.assertEqual(len(model_messages), len(messages))
        self.assertEqual(messages, original)
        self.assertEqual(model_messages[:3], messages[:3])
        self.assertEqual(model_messages[3].role, "user")
        self.assertEqual(model_messages[3].tool_results, ())
        self.assertIn(results[0].summary, model_messages[3].content)
        self.assertIn(results[1].summary, model_messages[3].content)
        self.assertNotIn(messages[3].content, model_messages[3].content)
        for result in results:
            self.assertNotIn(result.output, model_messages[3].content)
        self.assertEqual(messages[3].tool_results, results)

    def test_build_handles_summarized_and_unsummarized_results_without_mutation(self):
        summarized = ToolResult("read_file", "already summarized output", "Read configuration.")
        unsummarized = ToolResult("bash", "complete command output")
        another_result = ToolResult("read_file", "another full output")
        message = Message(role="user", content="Original history", tool_results=(summarized, unsummarized))
        another_message = Message(role="user", content="More history", tool_results=(another_result,))
        messages = [message, another_message, Message(role="assistant", content="Continuing")]
        original = deepcopy(messages)

        model_messages = ModelMessageBuilder().build(messages)

        content = model_messages[0].content
        self.assertIn(summarized.summary, content)
        self.assertNotIn(summarized.output, content)
        self.assertIn(unsummarized.output, content)
        self.assertIn(unsummarized.id, content)
        self.assertIn(another_result.output, model_messages[1].content)
        self.assertIn(another_result.id, model_messages[1].content)
        self.assertEqual(len(model_messages), len(messages) + 1)
        self.assertEqual(model_messages[-2], messages[-1])
        instruction = model_messages[-1]
        self.assertEqual(instruction.role, "system")
        self.assertIn(unsummarized.id, instruction.content)
        self.assertIn(another_result.id, instruction.content)
        self.assertNotIn(summarized.id, instruction.content)
        self.assertEqual(sum("concise semantic summary" in item.content for item in model_messages), 1)
        self.assertIn("continuing the main task", instruction.content)
        self.assertIn("100 to 200 tokens", instruction.content)
        self.assertIn("250 tokens", instruction.content)
        self.assertIn("fewer tokens for simple results", instruction.content)
        self.assertEqual(messages, original)
        self.assertEqual(message.content, "Original history")
        self.assertEqual(unsummarized.summary, "")
        self.assertEqual(model_messages[0].tool_results, ())

    def test_runner_keeps_and_sends_unsummarized_results_across_turns(self):
        for success in (True, False):
            with self.subTest(success=success):
                client = Mock()
                client.generate.side_effect = [
                    ModelResponse(tool_calls=[ToolCall("read_file", {"path": "config.py"})]),
                    ModelResponse(text="Done"),
                    ModelResponse(text="Next answer"),
                ]
                with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
                    runner = Runner(client)

                raw_output = "large raw output or error details"
                runner._tool_registry.execute = Mock(return_value=raw_output)
                if not success:
                    runner._tool_registry.execute.side_effect = ValueError(raw_output)

                self.assertEqual(runner.handle(Request.create("Read config.py")), "Done")
                session = runner._session_manager.current_session
                stored = next(message for message in session.messages if message.tool_results)
                result = stored.tool_results[0]
                self.assertEqual(result.output, raw_output)
                self.assertEqual(result.success, success)
                self.assertEqual(result.summary, "")
                self.assertIn(raw_output, stored.content)
                self.assertTrue(any("Raw tool calls:" in message.content for message in session.messages))
                self.assertEqual(session.messages[-1], Message(role="assistant", content="Done"))
                runner._tool_registry.execute.assert_called_once_with("read_file", {"path": "config.py"})

                self.assertEqual(runner.handle(Request.create("Continue")), "Next answer")
                for call in client.generate.call_args_list[1:]:
                    model_messages = call.args[0]
                    self.assertEqual(sum(raw_output in message.content for message in model_messages), 1)
                    self.assertTrue(any("concise semantic summary" in message.content for message in model_messages))
                    self.assertFalse(any(message.tool_results for message in model_messages))
                self.assertEqual(stored.tool_results[0].output, raw_output)

    def test_command_context_and_final_response_are_preserved(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(tool_calls=[ToolCall("read_file", {"path": "config.py"})]),
            ModelResponse(text='{"answer": "Done", "command_summary": "Read configuration."}'),
        ]
        command_context = Message(role="system", content="Command instructions")
        with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
            runner = Runner(client)
        runner._load_command_context = Mock(return_value=command_context)
        runner._tool_registry.execute = Mock(return_value="full configuration")

        self.assertEqual(runner.handle(Request.create("execute command review")), "Done")

        first_messages = client.generate.call_args_list[0].args[0]
        second_messages = client.generate.call_args_list[1].args[0]
        self.assertIn(command_context, first_messages)
        self.assertNotIn(command_context, second_messages)
        for messages in (first_messages, second_messages):
            self.assertTrue(any("`command_summary`" in message.content for message in messages))
        session = runner._session_manager.current_session
        self.assertEqual(session.messages[-1], Message(role="assistant", content="Done"))
        self.assertIn("Read configuration.", session.messages[-2].content)


if __name__ == "__main__":
    unittest.main()
