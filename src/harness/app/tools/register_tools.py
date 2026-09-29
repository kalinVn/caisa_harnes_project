from pathlib import Path

from harness.execution.tools.filesystem.read.tool import (
    ReadFileTool,
)
from harness.execution.tools.filesystem.write.tool import (
    WriteFileTool,
)
from harness.execution.tools.shell.execution.tool import (
    BashTool,
)
from harness.app.tools.tool_registry import (
    ToolRegistry,
)


def register_tools(
    registry: ToolRegistry,
    working_directory: Path | None = None,
) -> None:
    registry.register(
        ReadFileTool()
    )

    registry.register(
        WriteFileTool()
    )

    registry.register(
        BashTool(
            working_directory=working_directory
        )
    )
