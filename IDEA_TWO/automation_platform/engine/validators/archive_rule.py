from typing import Dict, Any
from .base_rule import BaseRule
from ..result_model import RuleResult

class ArchiveRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        
        queue_table = self.rule_config.get('queue_table')
        archive_table = self.rule_config.get('archive_table')
        lookup_key = context.get('lookup_key')
        
        try:
            with conn.cursor() as cursor:
                # Check if it's NOT in the queue table
                cursor.execute(f"SELECT count(*) FROM {queue_table} WHERE event_id = %s", (lookup_key,))
                in_queue = cursor.fetchone()[0] > 0
                
                # Check if it's IN the archive table
                cursor.execute(f"SELECT count(*) FROM {archive_table} WHERE event_id = %s", (lookup_key,))
                in_archive = cursor.fetchone()[0] > 0
            
            passed = not in_queue and in_archive
            
            return RuleResult(
                status='PASS' if passed else 'FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='archive',
                table=archive_table,
                expected='IN_ARCHIVE_NOT_IN_QUEUE',
                actual=f"in_queue={in_queue}, in_archive={in_archive}",
                message=f"Archive validation for {queue_table} -> {archive_table}"
            )
        except Exception as e:
            return RuleResult(
                status='FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='archive',
                table=archive_table,
                message=f"Error in ArchiveRule: {str(e)}"
            )
