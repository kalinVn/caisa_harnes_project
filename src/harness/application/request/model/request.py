from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class Request:
    message: str
    session_id: str
    created_at: datetime

    @classmethod
    def create(cls, message: str) -> "Request":
        return cls(
            message=message,
            session_id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
        )