import json
from pathlib import Path

from harness.app.loader.command_loader import (
    CommandLoader,
)
from harness.app.parser.command_parser import (
    parse_command,
)
from harness.app.resolver.command_resolver import (
    CommandResolver,
)
from harness.app.session_manager import (
    SessionManager,
)
from harness.app.models.request import Request
from harness.app.domain.command import Command
from harness.app.domain.message import Message
from harness.app.domain.session import Session
from harness.app.domain.tool_call import ToolCall
from harness.app.domain.tool_result import ToolResult
from harness.app.tools.tool_registry import (
    ToolRegistry,
)
from harness.app.tools.register_tools import (
    register_tools,
)
from harness.app.builder.model_message_builder import ModelMessageBuilder
from harness.app.models.tool_result_summary import ToolResultSummary
from harness.app.models.model_client import (
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

        session = self._session_manager.current_session

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

        if parsed_command is not None:
            turn_messages.append(
                self._build_command_response_format_context()
            )

        tool_steps = 0

        while tool_steps < self.MAX_TOOL_STEPS:
            # Example model_messages:
            # [
            #     Message(role="user", content="Read runner.py"),
            #     Message(role="assistant", content="I will read it."),
            #     Message(role="assistant", content="Raw tool calls: ..."),
            # ]

            model_messages = self._model_messages_builder.build(session.messages + turn_messages)
            

            if  tool_steps == 0 and command_message is not None :
                model_messages.append(command_message)

            response = self._model_client.generate(model_messages)
            self._apply_tool_result_summaries(session, response.tool_result_summaries)

            if not response.tool_calls:
                response_text = response.text

                if parsed_command is not None:
                    response_text, command_summary = self._parse_command_response(response.text)
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

                assistant_message = Message(role="assistant", content=response_text)
                session.add_message(assistant_message)

                return response_text

            session.add_message(
                Message(
                    role="assistant",
                    content=self._build_tool_calls_context(
                        response.tool_calls
                    ),
                )
            )

            tool_results: list[ToolResult] = []

            # Example response.tool_calls:
            # [ToolCall(
            #     name="read_file",
            #     arguments={"path": "src/harness/app/orchestrator.py"},
            # )]
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
                except Exception as error:
                    tool_result = ToolResult(
                        name=tool_call.name,
                        output=str(error),
                        success=False,
                    )

                tool_results.append(
                    tool_result
                )

            session.add_message(
                Message(
                    role="user",
                    content=self._build_tool_results_context(
                        tool_results
                    ),
                    tool_results=tuple(tool_results),
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

    def _apply_tool_result_summaries(self, session: Session, summaries: list[ToolResultSummary]) -> None:
        for summary in summaries:
            for message in session.messages:
                for result in message.tool_results:
                    if result.id == summary.id:
                        result.summary = summary.summary

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

    def _build_command_response_format_context(
        self,
    ) -> Message:
        return Message(
            role="system",
            content=(
                "When this command is complete and no more tools "
                "are needed, put a JSON-encoded object in the `text` string "
                "of the standard model response envelope. This inner object has "
                "exactly two string fields: `answer`, containing the "
                "normal user-facing response, and "
                "`command_summary`, containing one concise semantic "
                "sentence for durable history. Do not wrap the JSON "
                "in Markdown. Keep the outer `text`, `tool_calls`, and "
                "`tool_result_summaries` fields, including any summaries due. "
                "Do not include raw logs, file contents, "
                "or command instructions in `command_summary`. This "
                "format applies only to the final response; tool-call "
                "responses must continue to use the tool protocol."
            ),
        )

    def _parse_command_response(
        self,
        response_text: str,
    ) -> tuple[str, str]:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Command response did not follow the required "
                "JSON format."
            ) from error

        if not isinstance(payload, dict):
            raise ValueError(
                "Command response must be a JSON object."
            )

        answer = payload.get("answer")
        summary = payload.get("command_summary")

        if not isinstance(answer, str):
            raise ValueError(
                "Command response is missing a string answer."
            )

        if not isinstance(summary, str) or not summary.strip():
            raise ValueError(
                "Command response is missing a command summary."
            )

        return answer, summary.strip()

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

        command_path =  self._command_resolver.resolve(command_name)
        

        content = self._tool_registry.execute(
            "read_file",
            {
                "path": str(command_path),
            },
        )

        command = self._command_loader.load(content)

        command_context = self._build_command_context(command)
        

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

        for section_name, section_content in  command.sections.items():
            parts.append(
                f"{section_name}:\n"
                f"{section_content}"
            )

        return "\n\n".join(parts)
