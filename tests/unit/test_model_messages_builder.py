import unittest
from copy import deepcopy
from unittest.mock import Mock, patch
from uuid import UUID

from harness.builder.model_message_builder import ModelMessageBuilder
from harness.builder.tool_result_context_builder import (
    TOOL_RESULTS_CONTEXT_FOOTER,
    TOOL_RESULTS_CONTEXT_HEADER,
)
from harness.builder.tools_schema_builder import TOOLS_CONTEXT_HEADER
from harness.domain.message import Message
from harness.domain.tool_call import ToolCall
from harness.domain.tool_result import ToolResult
from harness.models.request import Request
from harness.models.response import ModelResponse
from harness.models.tool_result_summary import ToolResultSummary
from harness.orchestrator import Orchestrator
from harness.session_manager import SessionManager


class ModelMessageBuilderTest(unittest.TestCase):
    def test_tool_results_generate_unique_ids_and_allow_summary_assignment(self):
        first = ToolResult("read_file", "contents")
        second = ToolResult("read_file", "contents")

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(UUID(first.id).version, 4)
        self.assertEqual(UUID(second.id).version, 4)
        first.summary = "Read configuration."
        self.assertEqual(first.summary, "Read configuration.")

    def test_compose_preserves_history_and_replaces_only_tool_results(self):
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

        model_messages = ModelMessageBuilder().compose_model_messages(messages)

        self.assertIsNot(model_messages, messages)
        self.assertEqual(len(model_messages), len(messages))
        self.assertEqual(messages, original)
        self.assertEqual(model_messages[:3], messages[:3])
        self.assertEqual(model_messages[3].role, "user")
        self.assertEqual(model_messages[3].tool_results, ())
        self.assertIn(results[0].summary, model_messages[3].content)
        self.assertIn(results[1].summary, model_messages[3].content)
        self.assertIn(results[0].id, model_messages[3].content)
        self.assertIn(results[1].id, model_messages[3].content)
        self.assertNotIn(messages[3].content, model_messages[3].content)
        for result in results:
            self.assertNotIn(result.output, model_messages[3].content)
        self.assertEqual(messages[3].tool_results, results)
        self.assertEqual(model_messages[3].content.count(TOOL_RESULTS_CONTEXT_HEADER), 1)
        self.assertEqual(model_messages[3].content.count(TOOL_RESULTS_CONTEXT_FOOTER), 1)

    def test_compose_handles_summarized_and_unsummarized_results_without_mutation(self):
        summarized = ToolResult("read_file", "already summarized output", "Read configuration.")
        unsummarized = ToolResult("bash", "complete command output")
        another_result = ToolResult("read_file", "another full output")
        message = Message(role="user", content="Original history", tool_results=(summarized, unsummarized))
        another_message = Message(role="user", content="More history", tool_results=(another_result,))
        messages = [message, another_message, Message(role="assistant", content="Continuing")]
        original = deepcopy(messages)

        model_messages = ModelMessageBuilder().compose_model_messages(messages)

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

    def test_whitespace_summary_is_treated_as_missing_and_preserved(self):
        result = ToolResult(
            "bash",
            "complete command output",
            "  \n\t",
            id="whitespace-summary-id",
        )
        message = Message(role="user", content="Original history", tool_results=(result,))

        model_messages = ModelMessageBuilder().compose_model_messages([message])

        self.assertEqual(len(model_messages), 2)
        self.assertIn(result.output, model_messages[0].content)
        self.assertIn(result.id, model_messages[0].content)
        self.assertIn(result.id, model_messages[1].content)
        self.assertEqual(result.summary, "  \n\t")
        self.assertEqual(message.content, "Original history")
        self.assertIs(message.tool_results[0], result)

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
                    runner = Orchestrator(client)

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

    def test_runner_publishes_multiple_tool_results_once_in_execution_order(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(
                tool_calls=[
                    ToolCall("bash", {"command": "printf 'first\\nsecond\\n'"}),
                    ToolCall("read_file", {"path": "missing.txt"}),
                ]
            ),
            ModelResponse(text="Done"),
        ]
        listener = Mock()
        with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
            runner = Orchestrator(client, on_tool_result=listener)

        runner._tool_registry.execute = Mock(
            side_effect=["first\nsecond", ValueError("missing file")]
        )

        self.assertEqual(runner.handle(Request.create("Inspect the project")), "Done")

        session = runner._session_manager.current_session
        stored_message = next(message for message in session.messages if message.tool_results)
        first, second = stored_message.tool_results

        self.assertEqual(listener.call_count, 2)
        self.assertIs(listener.call_args_list[0].args[0], first)
        self.assertIs(listener.call_args_list[1].args[0], second)
        self.assertEqual(first.output, "first\nsecond")
        self.assertTrue(first.success)
        self.assertEqual(second.output, "missing file")
        self.assertFalse(second.success)
        self.assertEqual(first.summary, "")
        self.assertEqual(second.summary, "")

    def test_runner_publishes_each_result_before_executing_the_next_tool(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(
                tool_calls=[
                    ToolCall("bash", {"command": "first"}),
                    ToolCall("bash", {"command": "second"}),
                ]
            ),
            ModelResponse(text="Done"),
        ]
        listener = Mock()
        with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
            runner = Orchestrator(client, on_tool_result=listener)

        def execute(_name, arguments):
            if arguments["command"] == "second":
                self.assertEqual(listener.call_count, 1)
                self.assertEqual(listener.call_args.args[0].output, "first output")
            return f"{arguments['command']} output"

        runner._tool_registry.execute = Mock(side_effect=execute)

        self.assertEqual(runner.handle(Request.create("Run both")), "Done")
        self.assertEqual(listener.call_count, 2)

    def test_command_context_and_final_response_are_preserved(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(tool_calls=[ToolCall("read_file", {"path": "config.py"})]),
            ModelResponse(text='{"answer": "Done", "command_summary": "Read configuration."}'),
        ]
        command_context = Message(role="system", content="Command instructions")
        listener = Mock()
        with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
            runner = Orchestrator(client, on_tool_result=listener)
        runner._tool_registry.execute = Mock(return_value="full configuration")

        with patch("harness.orchestrator.get_command_message_obj", return_value=command_context):
            self.assertEqual(runner.handle(Request.create("execute command review")), "Done")

        first_messages = client.generate.call_args_list[0].args[0]
        second_messages = client.generate.call_args_list[1].args[0]
        self.assertIn(command_context, first_messages)
        self.assertIn(command_context, second_messages)
        for messages in (first_messages, second_messages):
            self.assertTrue(any("`command_summary`" in message.content for message in messages))
        session = runner._session_manager.current_session
        self.assertEqual(session.messages[-1], Message(role="assistant", content="Done"))
        self.assertIn("Read configuration.", session.messages[-2].content)
        published_result = listener.call_args.args[0]
        self.assertEqual(listener.call_count, 1)
        self.assertEqual(published_result.name, "read_file")
        self.assertEqual(published_result.output, "full configuration")

    def test_invalid_command_response_is_retried_without_entering_history(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(text=""),
            ModelResponse(
                text=(
                    '{"answer": "Done", '
                    '"command_summary": "Command completed."}'
                )
            ),
        ]
        command_context = Message(role="system", content="Command instructions")
        with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
            runner = Orchestrator(client)

        with patch("harness.orchestrator.get_command_message_obj", return_value=command_context):
            self.assertEqual(runner.handle(Request.create("execute command review")), "Done")

        self.assertEqual(client.generate.call_count, 2)
        retry_messages = client.generate.call_args_list[1].args[0]
        self.assertIn(command_context, retry_messages)
        self.assertFalse(
            any(
                message.content.startswith(TOOLS_CONTEXT_HEADER)
                for message in retry_messages
            )
        )
        self.assertTrue(
            any("previous command response" in message.content for message in retry_messages)
        )
        session = runner._session_manager.current_session
        self.assertFalse(any(message.content == "" for message in session.messages))
        self.assertEqual(session.messages[-1], Message(role="assistant", content="Done"))

    def test_summary_only_command_response_is_retried_for_final_answer(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(
                tool_calls=[ToolCall("write_file", {"path": "result.txt"})]
            ),
            ModelResponse(
                tool_result_summaries=[
                    ToolResultSummary("result-id", "The file was created.")
                ]
            ),
            ModelResponse(
                text=(
                    '{"answer": "Created result.txt", '
                    '"command_summary": "Created the requested file."}'
                )
            ),
        ]
        command_context = Message(role="system", content="Command instructions")
        with patch.object(SessionManager, "_load_system_prompt", return_value="Instructions"):
            runner = Orchestrator(client)
        runner._tool_registry.execute = Mock(return_value="full write output")

        with (
            patch("harness.orchestrator.get_command_message_obj", return_value=command_context),
            patch("harness.domain.tool_result.uuid4", return_value="result-id"),
        ):
            result = runner.handle(Request.create("execute command review"))

        self.assertEqual(result, "Created result.txt")
        self.assertEqual(client.generate.call_count, 3)
        final_messages = client.generate.call_args_list[2].args[0]
        self.assertTrue(
            any("The file was created." in message.content for message in final_messages)
        )
        self.assertFalse(
            any("full write output" in message.content for message in final_messages)
        )


if __name__ == "__main__":
    unittest.main()
