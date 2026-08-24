# src/harness/domain/commands/command/model.py

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    sections: dict[str, str] = field(default_factory=dict)