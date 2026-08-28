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
            self._tool_registry
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

        if parsed_command is not None:
            self._load_command_context(
                parsed_command.name
            )

        # self._debug_current_session()

        

        response = self._model_client.generate(
            session.messages
        )

        
        if response.tool_calls:
            tool_results: list[str] = []

            for tool_call in response.tool_calls:
                result = self._tool_registry.execute(
                    tool_call.name,
                    tool_call.arguments,
                )

                tool_results.append(
                    f"{tool_call.name}: {result}"
                )

            return "\n".join(tool_results)

        assistant_message = Message(
            role="assistant",
            content=response.text,
        )

        session.add_message(
            assistant_message
        )

        return response.text

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
    ) -> None:
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

        command_message = Message(
            role="system",
            content=command_context,
        )

        session = (
            self._session_manager.current_session
        )

        session.add_message(
            command_message
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
