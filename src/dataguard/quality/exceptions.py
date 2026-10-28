"""DataGuard Validation Exceptions Model."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional


@dataclass
class QualityException:
    run_id: str
    batch_id: str
    rule_id: str
    record_reference: str
    field_name: str
    invalid_value: Optional[str]
    severity: str
    issue_description: str
    exception_id: str = ""
    detected_at: Optional[datetime] = None
    resolution_status: str = "OPEN"

    def __post_init__(self):
        if not self.exception_id:
            self.exception_id = f"EXC_{uuid.uuid4().hex[:12].upper()}"
        if self.detected_at is None:
            self.detected_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if isinstance(data["detected_at"], datetime):
            data["detected_at"] = data["detected_at"].isoformat()
        return data
