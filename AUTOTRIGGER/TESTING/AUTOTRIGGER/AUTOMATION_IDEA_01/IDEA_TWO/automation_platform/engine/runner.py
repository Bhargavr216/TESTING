import os
import sys
import argparse
from typing import List, Dict, Any

from .suite_loader import SuiteLoader
from .service_registry import ServiceRegistry
from .db_factory import DatabaseFactory
from .rule_registry import RuleRegistry
from .state_executor import StateExecutor
from .report_builder import ReportBuilder

# Import all validators to ensure they are registered
from .validators.persistence_rule import PersistenceRule
from .validators.column_rule import ColumnRule
from .validators.json_rule import JsonRule
from .validators.retry_rule import RetryRule
from .validators.archive_rule import ArchiveRule
from .validators.custom_sql_rule import CustomSQLRule
from .validators.smart_rule import SmartRule
from .validators.audit_rule import AuditRule

class Runner:
    def __init__(self, suite_path: str):
        self.suite_path = suite_path
        self.suite_loader = SuiteLoader(suite_path)
        self.report_builder = ReportBuilder(self.suite_loader.get_suite_name())
        
        # Register rules
        RuleRegistry.register("persistence", PersistenceRule)
        RuleRegistry.register("column", ColumnRule)
        RuleRegistry.register("json", JsonRule)
        RuleRegistry.register("retry", RetryRule)
        RuleRegistry.register("archive", ArchiveRule)
        RuleRegistry.register("custom_sql", CustomSQLRule)
        RuleRegistry.register("smart_validate", SmartRule)
        RuleRegistry.register("audit_validate", AuditRule)

    def run(self, service_filter: str = None, type_filter: str = None):
        """
        Executes the entire suite with optional filters.
        """
        # Load service configuration
        ServiceRegistry.load()
        
        # Discover scenarios
        scenarios = self.suite_loader.discover_scenarios(service_filter, type_filter)
        print(f"Found {len(scenarios)} scenarios to execute.")
        
        for scenario_data in scenarios:
            service_name = scenario_data.get('service')
            scenario_no = scenario_data.get('scenario_no')
            
            print(f"Running scenario: {scenario_no} ({service_name})")
            
            # Get database connection for the service
            db_config_path = ServiceRegistry.get_db_config_path(service_name)
            if not db_config_path:
                print(f"No DB config found for service {service_name}. Skipping.")
                continue
                
            try:
                # 2. Get connection using DatabaseFactory (now supports Azure Connection Strings)
                conn = DatabaseFactory.get_connection(service_name, db_config_path)
                
                if not conn:
                    print(f"Skipping scenario {scenario_no} due to DB connection failure.")
                    continue

                # Execute states and rules (Pass full config instead of just path)
                with open(db_config_path, 'r') as f:
                    service_config = json.load(f)
                
                scenario_results = StateExecutor.execute_states(scenario_data, conn, service_config)
                self.report_builder.add_results(scenario_results)
                
            except Exception as e:
                print(f"Error executing scenario {scenario_no}: {e}")
                # We could add a FAIL result to the report here
                
            finally:
                # We could close the connection here, but we might want to keep it open
                # for the duration of the suite if multiple scenarios use the same service.
                # Requirement 11 says "Close after execution". Let's close it.
                DatabaseFactory.close_connection(service_name)
                
        # Generate final reports
        self.report_builder.generate_reports()

def main():
    parser = argparse.ArgumentParser(description="Enterprise Rule-Driven Validation Engine")
    parser.add_argument("--suite", default="suite.json", help="Path to suite.json")
    parser.add_argument("--service", help="Filter by service name")
    parser.add_argument("--type", help="Filter by test type")
    
    args = parser.parse_args()
    
    # Overrides from CLI if provided
    # (Implementation of overrides in suite_loader/suite.json would be better)
    
    runner = Runner(args.suite)
    runner.run(service_filter=args.service, type_filter=args.type)

if __name__ == "__main__":
    main()
