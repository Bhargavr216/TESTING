import json
from typing import Dict, Any, List
from .base_rule import BaseRule
from ..result_model import RuleResult

class JsonRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        lookup_key = context.get('lookup_key')
        
        table = self.rule_config.get('table')
        column = self.rule_config.get('column')
        expected_json = self.rule_config.get('expected_json', {})
        mandatory_fields = self.rule_config.get('mandatory_fields', [])
        ignored_paths = self.rule_config.get('ignored_paths', [])
        
        logs = [f"Starting JSON validation for table: {table}, column: {column}"]
        
        query = f"SELECT {column} FROM {table} WHERE event_id = %s"
        
        try:
            with conn.cursor() as cursor:
                logs.append(f"Executing query: {query} with key: {lookup_key}")
                cursor.execute(query, (lookup_key,))
                row = cursor.fetchone()
                
            if not row:
                logs.append("No record found in database.")
                return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                                 rule_type='json', table=table, column=column, message="No record found", logs=logs)
            
            actual_json = row[0]
            if isinstance(actual_json, str):
                actual_json = json.loads(actual_json)
            
            logs.append("JSON payload retrieved successfully.")
            failures = []
            
            # 1. Check Mandatory Fields
            for field in mandatory_fields:
                val = self._get_nested_val(actual_json, field)
                if val is None:
                    failures.append(f"Mandatory field missing: {field}")
                    logs.append(f"FAILURE: Mandatory field '{field}' is missing.")
                else:
                    logs.append(f"SUCCESS: Mandatory field '{field}' found.")

            # 2. Check Expected Values
            for path, expected_val in expected_json.items():
                if path in ignored_paths:
                    logs.append(f"Skipping ignored path: {path}")
                    continue
                
                actual_val = self._get_nested_val(actual_json, path)
                if actual_val != expected_val:
                    failures.append(f"Value mismatch at {path}")
                    logs.append(f"FAILURE: {path} - Expected: {expected_val}, Actual: {actual_val}")
                else:
                    logs.append(f"SUCCESS: {path} matches expected value.")
            
            passed = len(failures) == 0
            return RuleResult(
                status='PASS' if passed else 'FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='json',
                table=table,
                column=column,
                expected=expected_json,
                actual=actual_json,
                message="; ".join(failures) if not passed else "JSON validation passed",
                logs=logs
            )
        except Exception as e:
            logs.append(f"CRITICAL ERROR: {str(e)}")
            return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                             rule_type='json', table=table, message=str(e), logs=logs)

    def _get_nested_val(self, data, path):
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            elif isinstance(data, list):
                try:
                    data = data[int(key)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return data
