from typing import Dict, Any
from .base_rule import BaseRule
from ..result_model import RuleResult

class PersistenceRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        lookup_key = context.get('lookup_key')
        
        table = self.rule_config.get('table')
        expectation = self.rule_config.get('expectation')
        
        logs = [f"Starting persistence check for table: {table}", f"Lookup key: {lookup_key}"]
        
        query = f"SELECT count(*) FROM {table} WHERE event_id = %s"
        
        try:
            with conn.cursor() as cursor:
                logs.append(f"Executing query: {query}")
                cursor.execute(query, (lookup_key,))
                count = cursor.fetchone()[0]
            
            persisted = count > 0
            passed = (expectation == 'PERSIST' and persisted) or (expectation == 'NOT_PERSIST' and not persisted)
            
            actual_status = 'PERSISTED' if persisted else 'NOT_PERSISTED'
            logs.append(f"Record {actual_status} in {table}.")
            
            return RuleResult(
                status='PASS' if passed else 'FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='persistence',
                table=table,
                expected=expectation,
                actual=actual_status,
                message=f"Persistence check for {table} with expectation {expectation}",
                logs=logs
            )
        except Exception as e:
            logs.append(f"CRITICAL ERROR: {str(e)}")
            return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                             rule_type='persistence', table=table, message=str(e), logs=logs)
