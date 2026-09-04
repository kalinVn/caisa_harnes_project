import json
from pathlib import Path

from harness.application.commands.loader.loader import (
    CommandLoader,
)
from harness.application.commands.parser.parser import (
    parse_command,
)
from harness.application.commands.resolver.resolver import (
    CommandResolver,
)
from harness.application.orchestration.sessions.manager.manager import (
    SessionManager,
)
from harness.application.request.model.request import Request
from harness.domain.commands.model import Command
from harness.domain.messages.message.model import Message
from harness.domain.tool_calls.call.model import ToolCall
from harness.domain.tool_calls.result.model import ToolResult
from harness.execution.tools.registry.registry import (
    ToolRegistry,
)
from harness.execution.tools.registry.registration.registry import (
    register_tools,
)
from harness.intelligence.models.contracts.model.contract import (
    ModelClient,
)


class Runner:
    MAX_TOOL_STEPS = 20

    def __init__(
        self,
        model_client: ModelClient,
        project_root: Path | None = None,
    ) -> None:
        self._model_client = model_client

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

        register_tools(
            self._tool_registry,
            working_directory=self._project_root,
        )

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

        session = (
            self._session_manager.current_session
        )

        user_message = Message(
            role="user",
            content=request.message,
        )

        session.add_message(
            user_message
        )

        parsed_command = parse_command(
            request.message
        )

        command_message = None

        if parsed_command is not None:
            command_message = self._load_command_context(
                parsed_command.name
            )

        turn_messages: list[Message] = []
        tool_steps = 0

        while tool_steps < self.MAX_TOOL_STEPS:
            model_messages = (
                list(session.messages)
                + turn_messages
            )

            if (
                tool_steps == 0
                and command_message is not None
            ):
                model_messages.append(
                    command_message
                )

            response = self._model_client.generate(
                model_messages
            )

            if not response.tool_calls:
                assistant_message = Message(
                    role="assistant",
                    content=response.text,
                )

                session.add_message(
                    assistant_message
                )

                return response.text

            turn_messages.append(
                Message(
                    role="assistant",
                    content=self._build_tool_calls_context(
                        response.tool_calls
                    ),
                )
            )

            tool_results: list[ToolResult] = []

            for tool_call in response.tool_calls:
                if tool_steps >= self.MAX_TOOL_STEPS:
                    break

                tool_steps += 1

                try:
                    output = self._tool_registry.execute(
                        tool_call.name,
                        tool_call.arguments,
                    )

                    tool_result = ToolResult(
                        name=tool_call.name,
                        output=output,
                    )

                    # TODO: Let a future MemoryService
                    # select important tool outcomes.
                    session.add_message(
                        Message(
                            role="system",
                            content=(
                                self._build_execution_summary(
                                    tool_call.name,
                                    tool_call.arguments,
                                )
                            ),
                        )
                    )
                except Exception as error:
                    tool_result = ToolResult(
                        name=tool_call.name,
                        output=str(error),
                        success=False,
                    )

                tool_results.append(
                    tool_result
                )

            turn_messages.append(
                Message(
                    role="user",
                    content=self._build_tool_results_context(
                        tool_results
                    ),
                )
            )

        limit_message = (
            "Tool execution stopped after reaching "
            f"the limit of {self.MAX_TOOL_STEPS} steps."
        )

        session.add_message(
            Message(
                role="assistant",
                content=limit_message,
            )
        )

        return limit_message

    def _build_tool_calls_context(
        self,
        tool_calls: list[ToolCall],
    ) -> str:
        raw_calls = [
            {
                "tool": tool_call.name,
                "arguments": tool_call.arguments,
            }
            for tool_call in tool_calls
        ]

        return "Raw tool calls:\n" + json.dumps(
            raw_calls,
            ensure_ascii=False,
            default=str,
        )

    def _build_execution_summary(
        self,
        tool_name: str,
        arguments: dict[str, object],
    ) -> str:
        path = arguments.get("path")

        if tool_name == "write_file" and path:
            action = f"updated {path}"
        elif tool_name == "read_file" and path:
            action = f"read {path}"
        else:
            action = "completed successfully"

        return f"Tool execution summary: {tool_name} {action}."

    def _build_tool_results_context(
        self,
        tool_results: list[ToolResult],
    ) -> str:
        parts = [
            "The requested tools have finished.",
        ]

        for tool_result in tool_results:
            parts.append(
                "\n".join(
                    [
                        f"Tool: {tool_result.name}",
                        f"Success: {tool_result.success}",
                        "Output:",
                        tool_result.output,
                    ]
                )
            )

        parts.append(
            "Use these results to continue the task. "
            "If no more tools are needed, respond normally."
        )

        return "\n\n".join(parts)

    def _debug_current_session(
        self,
    ) -> None:
        session = (
            self._session_manager.current_session
        )

        print("\nSession debug")
        print(f"Session ID: {session.id}")
        print(f"Messages: {len(session.messages)}")

        for index, message in enumerate(
            session.messages,
            start=1,
        ):
            print("\n" + "=" * 60)
            print(f"Message {index}")
            print(f"Role: {message.role}")
            print("Content:")
            print(message.content)

    def _load_command_context(
        self,
        command_name: str,
    ) -> Message:
        command_path = (
            self._command_resolver.resolve(
                command_name
            )
        )

        content = self._tool_registry.execute(
            "read_file",
            {
                "path": str(command_path),
            },
        )

        command = self._command_loader.load(
            content
        )

        command_context = (
            self._build_command_context(
                command
            )
        )

        return Message(
            role="system",
            content=command_context,
        )

    def _build_command_context(
        self,
        command: Command,
    ) -> str:
        parts = [
            f"Executing command: {command.name}",
            f"Description:\n{command.description}",
        ]

        for section_name, section_content in (
            command.sections.items()
        ):
            parts.append(
                f"{section_name}:\n"
                f"{section_content}"
            )

        return "\n\n".join(parts)
