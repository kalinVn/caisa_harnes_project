from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResultSummary:
    id: str
    summary: str
