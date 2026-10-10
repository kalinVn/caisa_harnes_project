from collections.abc import Callable
from pathlib import Path

from harness.builder.command_response_format_context_builder import (
    build_command_response_format_context,
    build_command_response_retry_context,
)
from harness.builder.tool_call_context_builder import build_tool_calls_context
from harness.builder.tools_schema_builder import TOOLS_CONTEXT_HEADER
from harness.parser.command_response_parser import parse_command_response

from harness.builder.tool_result_context_builder import build_tool_results_context

from harness.loader.command_context_loader import get_command_message_obj

from harness.loader.command_loader import (
    CommandLoader,
)
from harness.parser.command_parser import (
    ParsedCommand,
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
from harness.domain.session import Session
from harness.domain.tool_call import ToolCall
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
from harness.models.response import ModelResponse


class Orchestrator:
    MAX_TOOL_STEPS = 20
    MAX_COMMAND_RESPONSE_RETRIES = 2

    def __init__(
        self,
        model_client: ModelClient,
        project_root: Path | None = None,
        on_tool_result: Callable[[ToolResult], None] | None = None,
    ) -> None:
        self._model_client = model_client
        self._model_messages_builder = ModelMessageBuilder()
        self._on_tool_result = on_tool_result

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

        # Подготвя съобщенията за модела, добавя временни инструкции и контекст за команда,
        # без да променя историята на сесията.
        model_messages = self._create_model_messages(
            session.messages,
            parsed_command,
        )
        tool_steps = 0
        command_response_retries = 0

        while True:
            response = self._model_client.generate(model_messages)

            session.apply_tool_result_summaries(
                response.tool_result_summaries
            )

            if not response.tool_calls:
                try:
                    return self._add_message_without_tool_calls(
                        session,
                        response,
                        parsed_command,
                    )
                except ValueError as error:
                    if parsed_command is None:
                        raise

                    if (
                        command_response_retries
                        >= self.MAX_COMMAND_RESPONSE_RETRIES
                    ):
                        raise ValueError(
                            "Command response remained invalid after "
                            f"{self.MAX_COMMAND_RESPONSE_RETRIES} retries."
                        ) from error

                    command_response_retries += 1
                    model_messages = self._create_model_messages(
                        session.messages,
                        parsed_command,
                        include_tools=False,
                    )
                    model_messages.append(
                        build_command_response_retry_context()
                    )
                    continue

            if tool_steps >= self.MAX_TOOL_STEPS:
                raise ValueError(
                    "Maximum tool execution steps exceeded."
                )

            session.add_message(
                Message(
                    role="assistant",
                    content=build_tool_calls_context(
                        response.tool_calls
                    ),
                    tool_result_output_requests=tuple(
                        response.tool_result_output_requests
                    ),
                )
            )

            tool_results = self._execute_tool_calls(
                response.tool_calls
            )

            session.add_message(
                Message(
                    role="user",
                    content=build_tool_results_context(tool_results),
                    tool_results=tuple(tool_results),
                )
            )

            tool_steps += 1
            model_messages = self._create_model_messages(
                session.messages,
                parsed_command,
            )

    def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
    ) -> list[ToolResult]:
        tool_results: list[ToolResult] = []

        for tool_call in tool_calls:
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

            if self._on_tool_result is not None:
                self._on_tool_result(tool_result)

        return tool_results

    def _create_model_messages(
        self,
        session_messages: list[Message],
        parsed_command: ParsedCommand | None,
        include_command_context: bool = True,
        include_tools: bool = True,
    ) -> list[Message]:
        command_message = None

        # Добавяме системно съобщение само за текущия ход, което указва на модела как да форматира
        # финалния отговор при команда. Това съобщение не се записва в историята на сесията и важи
        # само за конкретното извикване
        # Може да добавим – например, при команда за създаване на файл, инструктираме модела
        # финалният отговор да е  JSON с полета answer и command_summary. Това важи само за този ход
        # и не променя историята
        response_format_instruction: list[Message] = []

        if parsed_command is not None:
            response_format_instruction.append(
                build_command_response_format_context()
            )

            if include_command_context:
                command_message = get_command_message_obj(
                    parsed_command.name,
                    command_resolver=self._command_resolver,
                    tool_registry=self._tool_registry,
                    command_loader=self._command_loader,
                )

        messages_for_model = session_messages
        if not include_tools:
            messages_for_model = [
                message
                for message in session_messages
                if not (
                    message.role == "system"
                    and message.content.startswith(TOOLS_CONTEXT_HEADER)
                )
            ]

        model_messages = self._model_messages_builder.compose_model_messages(
            messages_for_model + response_format_instruction
        )

        if command_message is not None:
            model_messages.append(command_message)

        return model_messages

    def _add_message_without_tool_calls(
        self,
        session: Session,
        response: ModelResponse,
        parsed_command: ParsedCommand | None,
    ) -> str:
        response_text = response.text

        if parsed_command is not None:
            response_text, command_summary = parse_command_response(response.text)

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
            tool_result_output_requests=tuple(
                response.tool_result_output_requests
            ),
        )

        session.add_message(assistant_message)

        return response_text
