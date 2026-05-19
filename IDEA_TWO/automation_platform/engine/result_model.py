from dataclasses import dataclass, asdict
from typing import Optional, Any

@dataclass
class RuleResult:
    status: str  # PASS / FAIL
    service: str
    scenario: str
    state: str
    rule_type: str
    table: Optional[str] = None
    column: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    message: Optional[str] = None
    logs: Optional[List[str]] = None # Capture detailed logs for this rule execution

    def to_dict(self):
        return asdict(self)
