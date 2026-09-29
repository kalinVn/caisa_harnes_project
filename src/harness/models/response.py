from dataclasses import dataclass, field

from harness.domain.tool_call import ToolCall
from harness.models.tool_result_summary import ToolResultSummary


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_result_summaries: list[ToolResultSummary] = field(default_factory=list)