from dataclasses import dataclass
from typing import Literal

from harness.domain.tool_result import ToolResult


MessageRole = Literal["user", "assistant", "system"]


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str
    tool_results: tuple[ToolResult, ...] = ()
    tool_result_output_requests: tuple[str, ...] = ()
