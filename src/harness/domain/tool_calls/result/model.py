from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    name: str
    output: str
    success: bool = True
