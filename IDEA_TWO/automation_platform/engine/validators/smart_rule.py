import json
from typing import Dict, Any, List
from .base_rule import BaseRule
from ..result_model import RuleResult

class SmartRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        default_lookup = context.get('lookup_key')
        resolved_lookups = context.get('resolved_lookups', {})
        
        validations_config = self.rule_config.get('validations', {})
        
        structured_logs = []
        all_passed = True
        total_failures = []

        # Handle "tables_persistance_check" if it exists
        persistence_summary = validations_config.get('tables_persistance_check', {})
        
        # Merge persistence checks into the main validation loop
        tables_to_validate = list(validations_config.keys())
        if 'tables_persistance_check' in tables_to_validate:
            tables_to_validate.remove('tables_persistance_check')
            # Add tables from persistence check that aren't in the main list
            for t in persistence_summary.keys():
                if t not in tables_to_validate:
                    tables_to_validate.append(t)

        for table_name in tables_to_validate:
            checks = validations_config.get(table_name, {})
            p_check = persistence_summary.get(table_name, {})
            
            # Determine which lookup ID to use for this table
            look_up_id_name = checks.get('look_up_id', p_check.get('look_up_id'))
            lookup_val = resolved_lookups.get(look_up_id_name, default_lookup)
            
            # 1. Fetch record
            query = f"SELECT * FROM {table_name} WHERE {look_up_id_name or 'event_id'} = %s"
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (lookup_val,))
                    row = cursor.fetchone()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                row_data = dict(zip(columns, row)) if row else None
                
                # Persistence check (from shorthand or from tables_persistance_check)
                persistence_req = p_check.get('persistance', checks.get('!PERSISTENCE', 'PERSIST'))
                persisted = row_data is not None
                
                p_passed = (persistence_req == 'PERSIST' and persisted) or (persistence_req == 'NOT_PERSIST' and not persisted)
                structured_logs.append({
                    "table": table_name,
                    "path": f"PERSISTENCE ({look_up_id_name or 'event_id'}={lookup_val})",
                    "expected": persistence_req,
                    "actual": "EXISTS" if persisted else "MISSING",
                    "status": "PASS" if p_passed else "FAIL"
                })
                if not p_passed: all_passed = False

                if persisted:
                    # 2. Process all other checks in the table dict
                    for path, expected_val in checks.items():
                        if path in ['look_up_id', '!PERSISTENCE']: continue
                        
                        actual_val = None
                        if '.' in path:
                            col_name, nested_path = path.split('.', 1)
                            json_blob = row_data.get(col_name)
                            if isinstance(json_blob, str):
                                json_blob = json.loads(json_blob)
                            actual_val = self._get_nested(json_blob, nested_path)
                        else:
                            actual_val = row_data.get(path)

                        match = (actual_val == expected_val) if expected_val != "!MANDATORY" else actual_val is not None
                        structured_logs.append({
                            "table": table_name,
                            "path": path,
                            "expected": expected_val,
                            "actual": actual_val,
                            "status": "PASS" if match else "FAIL"
                        })
                        if not match: 
                            all_passed = False
                            total_failures.append(f"{table_name}.{path} mismatch")
            except Exception as e:
                all_passed = False
                structured_logs.append({"table": table_name, "path": "ERROR", "expected": "N/A", "actual": str(e), "status": "FAIL"})

        return RuleResult(
            status='PASS' if all_passed else 'FAIL',
            service=service,
            scenario=scenario,
            state=state,
            rule_type='smart_validate',
            message="; ".join(total_failures) if total_failures else "All validations passed.",
            logs=[json.dumps(log) for log in structured_logs]
        )

    def _get_nested(self, data, path):
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict): data = data.get(key)
            elif isinstance(data, list):
                try: data = data[int(key)]
                except: return None
            else: return None
        return data
