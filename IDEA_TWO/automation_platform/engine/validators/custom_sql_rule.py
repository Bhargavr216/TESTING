from typing import Dict, Any
from .base_rule import BaseRule
from ..result_model import RuleResult

class CustomSQLRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        
        query = self.rule_config.get('query')
        expected_result = self.rule_config.get('expected_result') # e.g. "SUCCESS", or a specific value
        lookup_key = context.get('lookup_key')
        
        try:
            with conn.cursor() as cursor:
                # Replace lookup_key placeholder if present
                formatted_query = query.replace('%event_id%', str(lookup_key))
                cursor.execute(formatted_query)
                row = cursor.fetchone()
                
            if not row:
                actual_val = None
            else:
                actual_val = row[0]
            
            passed = str(actual_val) == str(expected_result)
            
            return RuleResult(
                status='PASS' if passed else 'FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='custom_sql',
                expected=str(expected_result),
                actual=str(actual_val),
                message=f"Custom SQL validation for {query}"
            )
        except Exception as e:
            return RuleResult(
                status='FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='custom_sql',
                message=f"Error in CustomSQLRule: {str(e)}"
            )
