from dataclasses import dataclass, field

from harness.app.domain.tool_call import ToolCall
from harness.app.models.tool_result_summary import ToolResultSummary


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_result_summaries: list[ToolResultSummary] = field(default_factory=list)