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
    MAX_TOOL_RESULT_OUTPUT_REQUEST_STEPS = 3
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
        tool_steps = 0
        command_response_retries = 0
        tool_result_output_request_steps = 0
        
        if not request.message.strip():
            return "Please enter a message."
        
        session = self._session_manager.current_session
        user_message = Message(role="user", content=request.message)
        session.add_message(user_message)
        parsed_command = parse_command(request.message)

        # Prepare model messages with temporary instructions and command
        # context without modifying the session history.
        model_messages = self._create_model_messages(
            session.messages,
            parsed_command,
        )
        
        while True:
            response = self._model_client.generate(model_messages)
            
            session.apply_tool_result_summaries(response.tool_result_summaries)
            requested_tool_result_ids: list[str] = []
            
            for result_id in response.tool_result_output_requests:
                tool_result = session.get_tool_result_by_id(result_id)
                if tool_result is not None:
                    requested_tool_result_ids.append(tool_result.id)

            if not response.tool_calls:
                if requested_tool_result_ids:
                    updated_model_messages = (
                        self._model_messages_builder
                        .update_model_messages_by_tool_result_output_requests_ids(
                            model_messages=model_messages,
                            tool_result_output_requests=(
                                requested_tool_result_ids
                            ),
                        )
                    )

                    if updated_model_messages is not model_messages:
                        if tool_result_output_request_steps >= self.MAX_TOOL_RESULT_OUTPUT_REQUEST_STEPS:
                            message = (
                                "Maximum tool result output request steps "
                                "exceeded."
                            )
                            session.add_message(
                                Message(role="assistant", content=message)
                            )
                            return message

                        tool_result_output_request_steps += 1
                        model_messages = updated_model_messages
                        continue

                # A str is the final user response. A list[Message] is updated
                # context with JSON correction instructions for the next call.
                result = self._handle_response_without_tool_calls(
                    session,
                    response,
                    parsed_command,
                    command_response_retries,
                )

                if isinstance(result, str):
                    return result
                
                command_response_retries += 1
                model_messages = result

                continue

            if tool_steps >= self.MAX_TOOL_STEPS:

                message = "Maximum tool execution steps exceeded."
                session.add_message(Message(role="assistant", content=message))

                return message
            
            session.add_message(
                Message(
                    role="assistant",
                    content=build_tool_calls_context(response.tool_calls),
                )
            )

            tool_results = self._execute_tool_calls(response.tool_calls)

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

            if requested_tool_result_ids:
                model_messages = (self._model_messages_builder.update_model_messages_by_tool_result_output_requests_ids(
                        model_messages=model_messages,
                        tool_result_output_requests=(
                            requested_tool_result_ids
                        )
                    )
                )

    def _handle_response_without_tool_calls(
        self,
        session: Session,
        response: ModelResponse,
        parsed_command: ParsedCommand | None,
        command_response_retries: int,
    ) -> str | list[Message]:
        # For a regular message, store the response without command handling.
        if parsed_command is None:
            self._add_response_message(session, response)
            return response.text

        # Parse the command response and verify that it has the expected form.
        parsed_response = parse_command_response(response.text)

        if parsed_response is not None:

            answer, command_summary = parsed_response

            # Store command_summary as a system message.
            self._add_command_summary_message(session, parsed_command, command_summary)
            session.add_message(Message(role="assistant", content=answer))

            # Return the final text intended for the user.
            return answer

        # After all correction attempts are exhausted, store and return an
        # error message.
        if command_response_retries >= self.MAX_COMMAND_RESPONSE_RETRIES:
            message = (
                "Command response remained invalid after "
                f"{self.MAX_COMMAND_RESPONSE_RETRIES} retries."
            )

            session.add_message(Message(role="assistant", content=message))

            return message


        model_messages = self._create_model_messages(
            session.messages,
            parsed_command,
            include_tools=False,
        )
        model_messages.append(build_command_response_retry_context())

        return model_messages

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
        include_tools: bool = True,
    ) -> list[Message]:
        """Build model messages for the current request.

        For commands, add a temporary system message describing the required
        final response format and append the resolved command context. These
        temporary messages apply only to the current call and are not stored in
        the session history. Tool definitions can be excluded for correction
        retries.
        """
        command_message = None
        # Add a per-call format instruction for command responses without
        # storing it in the session history.
        response_format_instruction: list[Message] = []
        if parsed_command is not None:
            response_format_instruction.append(build_command_response_format_context())
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

    def _add_response_message(self, session: Session, response: ModelResponse) -> None:
        """Store a regular final response that is not associated with a command."""

        session.add_message(
            Message(
                role="assistant",
                content=response.text,
            )
        )
    def _add_command_summary_message(
        self,
        session: Session,
        parsed_command: ParsedCommand,
        command_summary: str,
    ) -> None:
        """Store the summary of an already validated command response."""
        session.add_message(
            Message(
                role="system",
                content=(
                    "Command execution summary: "
                    f"{parsed_command.name} was executed. Result: "
                    f"{command_summary}"
                ),
            )
        )
