from harness.execution.tools.filesystem.read.tool import (
    ReadFileTool,
)
from harness.execution.tools.filesystem.write.tool import (
    WriteFileTool,
)
from harness.execution.tools.shell.execution.tool import (
    BashTool,
)
from harness.execution.tools.registry.registry import (
    ToolRegistry,
)


def register_tools(
    registry: ToolRegistry,
) -> None:
    registry.register(
        ReadFileTool()
    )

    registry.register(
        WriteFileTool()
    )

    registry.register(
        BashTool()
    )
