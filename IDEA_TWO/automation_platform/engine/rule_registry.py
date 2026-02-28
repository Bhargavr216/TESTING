from typing import Dict, Type, Any

class RuleRegistry:
    _rules: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, rule_type: str, rule_class: Type[Any]):
        """
        Registers a rule class by its type.
        """
        cls._rules[rule_type] = rule_class

    @classmethod
    def get_rule_class(cls, rule_type: str) -> Type[Any]:
        """
        Retrieves a registered rule class by its type.
        """
        if rule_type not in cls._rules:
            raise ValueError(f"No rule registered for type: {rule_type}")
        return cls._rules[rule_type]

    @classmethod
    def execute_rule(cls, rule_config: Dict[str, Any], **context) -> Any:
        """
        Executes a rule by looking up its class and calling its validate method.
        """
        rule_type = rule_config.get('type')
        if not rule_type:
            raise ValueError("Rule config missing 'type' field")
        
        rule_class = cls.get_rule_class(rule_type)
        rule_instance = rule_class(rule_config)
        return rule_instance.validate(**context)
