import unittest
from unittest.mock import Mock, patch

from harness.domain.message import Message
from harness.domain.tool_call import ToolCall
from harness.models.request import Request
from harness.models.response import ModelResponse
from harness.orchestrator import Orchestrator
from harness.session_manager import SessionManager


class OrchestratorToolServiceIntegrationTest(unittest.TestCase):
    def create_orchestrator(
        self,
        client: Mock,
        on_tool_result=None,
    ) -> Orchestrator:
        with patch.object(
            SessionManager,
            "_load_system_prompt",
            return_value="Instructions",
        ):
            return Orchestrator(client, on_tool_result=on_tool_result)

    def test_tool_service_reuses_orchestrator_dependencies(self):
        callback = Mock()
        runner = self.create_orchestrator(Mock(), callback)

        self.assertIs(runner._tool_service._tool_registry, runner._tool_registry)
        self.assertIs(
            runner._tool_service._model_message_builder,
            runner._model_messages_builder,
        )
        self.assertIs(runner._tool_service._on_tool_result, callback)

    def test_tool_messages_keep_execution_order_and_final_response(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(
                tool_calls=[
                    ToolCall("read_file", {"path": "first.txt"}),
                    ToolCall("bash", {"command": "pwd"}),
                ]
            ),
            ModelResponse(text="Done"),
        ]
        callback = Mock()
        runner = self.create_orchestrator(client, callback)
        session = runner._session_manager.current_session

        def execute(name, _arguments):
            self.assertTrue(session.messages[-1].content.startswith("Raw tool calls:"))
            self.assertFalse(session.messages[-1].tool_results)
            return f"{name} output"

        runner._tool_registry.execute = Mock(side_effect=execute)

        result = runner.handle(Request.create("Inspect the project"))

        self.assertEqual(result, "Done")
        self.assertEqual(runner._tool_registry.execute.call_count, 2)
        self.assertEqual(callback.call_count, 2)
        tool_call_index = next(
            index
            for index, message in enumerate(session.messages)
            if message.content.startswith("Raw tool calls:")
        )
        tool_result_index = next(
            index
            for index, message in enumerate(session.messages)
            if message.tool_results
        )
        self.assertLess(tool_call_index, tool_result_index)
        self.assertEqual(len(session.messages[tool_result_index].tool_results), 2)
        self.assertEqual(session.messages[-1], Message(role="assistant", content="Done"))

    def test_tool_execution_limit_is_preserved(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(tool_calls=[ToolCall("read_file")]),
            ModelResponse(tool_calls=[ToolCall("read_file")]),
        ]
        runner = self.create_orchestrator(client)
        runner.MAX_TOOL_STEPS = 1
        runner._tool_registry.execute = Mock(return_value="output")

        result = runner.handle(Request.create("Continue"))

        self.assertEqual(result, "Maximum tool execution steps exceeded.")
        runner._tool_registry.execute.assert_called_once_with("read_file", {})
        self.assertEqual(
            runner._session_manager.current_session.messages[-1],
            Message(role="assistant", content=result),
        )

    def test_command_response_retry_limit_and_final_result_are_preserved(self):
        client = Mock()
        client.generate.side_effect = [
            ModelResponse(text="invalid"),
            ModelResponse(text="still invalid"),
        ]
        runner = self.create_orchestrator(client)
        runner.MAX_COMMAND_RESPONSE_RETRIES = 1

        with patch(
            "harness.orchestrator.get_command_message_obj",
            return_value=Message(role="system", content="Command instructions"),
        ):
            result = runner.handle(Request.create("execute command review"))

        self.assertEqual(
            result,
            "Command response remained invalid after 1 retries.",
        )
        self.assertEqual(client.generate.call_count, 2)
        self.assertEqual(
            runner._session_manager.current_session.messages[-1],
            Message(role="assistant", content=result),
        )


if __name__ == "__main__":
    unittest.main()
