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
from harness.application.request.model.request import Request
from harness.domain.messages.message.model import Message
from harness.domain.sessions.session.model import Session
from harness.execution.tools.filesystem.read.tool import (
    ReadFileTool,
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
        self._session = Session()

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
        self._read_file_tool = ReadFileTool()

    def handle(
        self,
        request: Request,
    ) -> str:
        if not request.message.strip():
            return "Please enter a message."

        user_message = Message(
            role="user",
            content=request.message,
        )

        self._session.add_message(
            user_message
        )

        parsed_command = parse_command(
            request.message
        )

        if parsed_command is not None:
            self._load_command_context(
                parsed_command.name
            )

        response_text = self._model_client.generate(
            self._session.messages
        )

        assistant_message = Message(
            role="assistant",
            content=response_text,
        )

        self._session.add_message(
            assistant_message
        )

        return response_text

    def _load_command_context(
        self,
        command_name: str,
    ) -> None:
        command_path = (
            self._command_resolver.resolve(
                command_name
            )
        )

        content = self._read_file_tool.execute(
            command_path
        )

        command = self._command_loader.load(
            content
        )

        command_context = self._build_command_context(
            command
        )

        command_message = Message(
            role="system",
            content=command_context,
        )
        

        self._session.add_message(
            command_message
        )

    def _build_command_context(
        self,
        command,
    ) -> str:
        parts = [
            f"Executing command: {command.name}",
            f"Description:\n{command.description}",
        ]

        for section_name, section_content in command.sections.items():
            parts.append(
                f"{section_name}:\n{section_content}"
            )

        return "\n\n".join(parts)
