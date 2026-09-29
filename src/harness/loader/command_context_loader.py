from harness.builder.command_context_builder import build_command_context
from harness.domain.message import Message
from harness.loader.command_loader import CommandLoader
from harness.resolver.command_resolver import CommandResolver
from harness.tools.tool_registry import ToolRegistry


def load_command_context(
    command_name: str,
    command_resolver: CommandResolver,
    tool_registry: ToolRegistry,
    command_loader: CommandLoader,
) -> Message:
    command_path = command_resolver.resolve(command_name)

    content = tool_registry.execute(
        "read_file",
        {
            "path": str(command_path),
        },
    )

    command = command_loader.load(content)

    command_context = build_command_context(command)

    return Message(
        role="system",
        content=command_context,
    )
