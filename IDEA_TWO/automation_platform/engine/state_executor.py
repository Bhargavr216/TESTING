import time
from typing import List, Dict, Any
from .rule_registry import RuleRegistry
from .result_model import RuleResult

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
    def execute_states(scenario_data: Dict[str, Any], conn: Any) -> List[RuleResult]:
        """
        Executes rules for each state in the scenario.
        """
        scenario_results = []
        service = scenario_data.get('service')
        scenario_no = scenario_data.get('scenario_no')
        states = scenario_data.get('states', [])
        
        # In a real engine, we'd trigger the event first, but the requirements focus on rule validation.
        # Let's assume the event has been triggered or we just validate the resulting state.
        # We need a lookup_key, let's assume it's part of the scenario_data for now, or extracted from the event file.
        # For simplicity, let's assume scenario_no is the event_id for now or there's a specific lookup_key.
        lookup_key = scenario_data.get('lookup_key', scenario_no)

        for state_config in states:
            state_name = state_config.get('name')
            wait_config = state_config.get('wait', {})
            timeout = wait_config.get('timeout', 0)
            interval = wait_config.get('interval', 2)
            
            # 1. Trigger Event Payload if present
            event_payload = state_config.get('event_payload')
            look_up_ref = state_config.get('look_up_ref', {})
            
            resolved_lookups = {}
            if event_payload:
                # Extract values based on look_up_ref
                payload_data = event_payload[0] if isinstance(event_payload, list) else event_payload
                for payload_key, db_column in look_up_ref.items():
                    val = StateExecutor._get_nested_payload(payload_data, payload_key)
                    if val:
                        resolved_lookups[db_column] = val

            rules = state_config.get('rules', [])
            
            # Wait if timeout is specified
            if timeout > 0:
                time.sleep(timeout) # Simplified: should actually poll until success or timeout

            for rule_config in rules:
                try:
                    context = {
                        'service': service,
                        'scenario': scenario_no,
                        'state': state_name,
                        'conn': conn,
                        'lookup_key': lookup_key,
                        'resolved_lookups': resolved_lookups,
                        'look_up_ref': look_up_ref
                    }
                    
                    result = RuleRegistry.execute_rule(rule_config, **context)
                    # If it's a SmartRule, we want to see the detailed structured logs
                    if result.rule_type == 'smart_validate':
                        # The results are already stored in the result object for the report builder
                        pass
                    
                    scenario_results.append(result)
                    
                    # If a critical rule fails, should we stop the scenario?
                    # For now, let's just keep going and collect all results.
                    
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
