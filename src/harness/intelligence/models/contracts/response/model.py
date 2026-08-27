from dataclasses import dataclass, field

from harness.domain.tool_calls.call.model import ToolCall


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)