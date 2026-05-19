import time
from typing import List, Dict, Any
from .rule_registry import RuleRegistry
from .result_model import RuleResult
from .azure_trigger import AzureEventHubProducer
from .db_factory import DBFactory

class StateExecutor:
    @staticmethod
    def _get_nested_payload(data: Any, path: str) -> Any:
        if not path or not data:
            return None
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                idx = int(key)
                current = current[idx] if 0 <= idx < len(current) else None
            else:
                return None
        return current

    @staticmethod
    def execute_states(scenario_data: Dict[str, Any], conn: Any, service_config: Dict[str, Any]) -> List[RuleResult]:
        """
        Executes all states in a scenario sequentially.
        """
        scenario_results = []
        service = scenario_data.get('service')
        scenario_no = scenario_data.get('scenario_no')
        states = scenario_data.get('states', [])
        lookup_key = scenario_data.get('lookup_key', scenario_no)

        for state_config in states:
            state_name = state_config.get('name', 'Unknown')
            
            # 1. Trigger REAL Azure Event Hub Event if present
            event_payload = state_config.get('event_payload')
            look_up_ref = state_config.get('look_up_ref', {})
            
            if event_payload and service_config.get('event_hub'):
                eh_config = service_config['event_hub']
                AzureEventHubProducer.trigger_event(
                    eh_config['connection_string'],
                    eh_config['event_hub_name'],
                    event_payload
                )

            resolved_lookups = {}
            if event_payload:
                # Extract values based on look_up_ref for validation lookup
                payload_data = event_payload[0] if isinstance(event_payload, list) else event_payload
                for payload_key, db_column in look_up_ref.items():
                    val = StateExecutor._get_nested_payload(payload_data, payload_key)
                    if val:
                        resolved_lookups[db_column] = val

            rules = state_config.get('rules', [])
            for rule_config in rules:
                try:
                    context = {
                        'service': service,
                        'scenario': scenario_no,
                        'state': state_name,
                        'conn': conn,
                        'lookup_key': lookup_key,
                        'resolved_lookups': resolved_lookups,
                        'look_up_ref': look_up_ref,
                        'schema': service_config.get('schema', 'public') # Pass schema to context
                    }
                    
                    result = RuleRegistry.execute_rule(rule_config, **context)
                    scenario_results.append(result)
                    
                except Exception as e:
                    # Capture rule execution error
                    scenario_results.append(RuleResult(
                        status='FAIL',
                        service=service,
                        scenario=scenario_no,
                        state=state_name,
                        rule_type=rule_config.get('type', 'unknown'),
                        message=f"Rule execution error: {str(e)}"
                    ))
                    
        return scenario_results
