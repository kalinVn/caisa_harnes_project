from dataclasses import dataclass, field
from uuid import uuid4

from harness.domain.message import Message
from harness.models.tool_result_summary import ToolResultSummary


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid4()))
    messages: list[Message] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def apply_tool_result_summaries(
        self,
        summaries: list[ToolResultSummary],
    ) -> None:
        for summary in summaries:
            for message in self.messages:
                for result in message.tool_results:
                    if result.id == summary.id:
                        result.summary = summary.summary
