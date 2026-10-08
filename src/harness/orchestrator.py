from pathlib import Path

from harness.builder.command_response_format_context_builder import (
    build_command_response_format_context,
)
from harness.builder.tool_call_context_builder import build_tool_calls_context
from harness.parser.command_response_parser import parse_command_response

from harness.builder.tool_result_context_builder import build_tool_results_context

from harness.loader.command_context_loader import load_command_context

from harness.loader.command_loader import (
    CommandLoader,
)
from harness.parser.command_parser import (
    parse_command,
)
from harness.resolver.command_resolver import (
    CommandResolver,
)
from harness.session_manager import (
    SessionManager,
)
from harness.models.request import Request
from harness.domain.message import Message
from harness.domain.tool_result import ToolResult
from harness.tools.tool_registry import (
    ToolRegistry,
)
from harness.tools.register_tools import (
    register_tools,
)
from harness.builder.model_message_builder import ModelMessageBuilder
from harness.models.model_client import (
    ModelClient,
)


class Orchestrator:
    MAX_TOOL_STEPS = 20

    def __init__(
        self,
        model_client: ModelClient,
        project_root: Path | None = None,
    ) -> None:
        self._model_client = model_client
        self._model_messages_builder = ModelMessageBuilder()

        self._project_root = (
            project_root or Path.cwd()
        )

        commands_directory = (
            self._project_root
            / ".caisa"
            / "commands"
        )

        self._command_resolver = CommandResolver(
            commands_directory
        )

        self._command_loader = CommandLoader()

        self._tool_registry = ToolRegistry()

        register_tools(self._tool_registry, working_directory=self._project_root)

        self._session_manager = SessionManager(
            project_root=self._project_root,
            tool_registry=self._tool_registry,
        )

        self._session_manager.create_session()

    def handle(
        self,
        request: Request,
    ) -> str:
        if not request.message.strip():
            return "Please enter a message."

        session = self._session_manager.current_session

        user_message = Message(role="user", content=request.message)
        session.add_message(user_message)

        parsed_command = parse_command(request.message)

        command_message = None
        turn_messages: list[Message] = []

        if parsed_command is not None:
            command_message = load_command_context(
                parsed_command.name,
                command_resolver=self._command_resolver,
                tool_registry=self._tool_registry,
                command_loader=self._command_loader,
            )

            turn_messages.append(
                build_command_response_format_context()
            )

        model_messages = self._model_messages_builder.build(
            session.messages + turn_messages
        )

        if command_message is not None:
            model_messages.append(command_message)

        response = self._model_client.generate(model_messages)

        session.apply_tool_result_summaries(
            response.tool_result_summaries
        )

        if not response.tool_calls:
            response_text = response.text

            if parsed_command is not None:
                response_text, command_summary = (
                    parse_command_response(
                        response.text
                    )
                )

                session.add_message(
                    Message(
                        role="system",
                        content=(
                            "Command execution summary: "
                            f"{parsed_command.name} was "
                            "executed. Result: "
                            f"{command_summary}"
                        ),
                    )
                )

            assistant_message = Message(
                role="assistant",
                content=response_text,
            )

            session.add_message(assistant_message)

            return response_text

        session.add_message(
            Message(
                role="assistant",
                content=build_tool_calls_context(
                    response.tool_calls
                ),
            )
        )

        tool_results: list[ToolResult] = []

        for tool_call in response.tool_calls:
            try:
                output = self._tool_registry.execute(
                    tool_call.name,
                    tool_call.arguments,
                )

                tool_result = ToolResult(
                    name=tool_call.name,
                    output=output,
                )

            except Exception as error:
                tool_result = ToolResult(
                    name=tool_call.name,
                    output=str(error),
                    success=False,
                )

            tool_results.append(tool_result)

        session.add_message(
            Message(
                role="user",
                content=build_tool_results_context(
                    tool_results
                ),
                tool_results=tuple(tool_results),
            )
        )

        return response.text
