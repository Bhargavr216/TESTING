from abc import ABC, abstractmethod
from typing import Any, Dict
from ..result_model import RuleResult

class BaseRule(ABC):
    def __init__(self, rule_config: Dict[str, Any]):
        self.rule_config = rule_config

    @abstractmethod
    def validate(self, **context) -> RuleResult:
        """
        Validates the rule and returns a RuleResult.
        Context will contain: service, scenario, state, conn, etc.
        """
        pass
