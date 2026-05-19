import json
import os
import glob
from typing import List, Dict, Any
from .service_registry import ServiceRegistry

class SuiteLoader:
    def __init__(self, suite_path: str):
        self.suite_path = suite_path
        self.suite_config = self._load_suite_config()

    def _load_suite_config(self) -> Dict[str, Any]:
        with open(self.suite_path, 'r') as f:
            return json.load(f)

    def discover_scenarios(self, service_filter: str = None, type_filter: str = None) -> List[Dict[str, Any]]:
        """
        Discovers scenarios based on suite.json filters and optional CLI overrides.
        """
        execution_config = self.suite_config.get('execution', {})
        
        # Use filter from CLI if provided, otherwise from suite.json
        services_to_run = [service_filter] if service_filter else execution_config.get('services', [])
        test_types_to_run = [type_filter] if type_filter else execution_config.get('test_types', [])
        
        scenario_source = self.suite_config.get('scenario_source', {})
        base_folder = scenario_source.get('base_folder', 'scenarios')
        auto_discover = scenario_source.get('auto_discover', True)
        
        if not auto_discover:
            # If auto-discover is false, we might want to load specific scenarios listed in suite.json
            # But the requirement says "No manual listing of scenarios".
            pass

        all_scenarios = []
        
        # Get base path for scenarios
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scenarios_base_path = os.path.join(project_root, base_folder)

        # Loop through services to run
        for service_name in (services_to_run if services_to_run else ServiceRegistry.list_services()):
            service_scenario_path = os.path.join(scenarios_base_path, service_name.lower())
            
            if not os.path.exists(service_scenario_path):
                continue
                
            # Find all JSON files in the service directory
            scenario_files = glob.glob(os.path.join(service_scenario_path, "*.json"))
            
            for file_path in scenario_files:
                with open(file_path, 'r') as f:
                    scenario_data = json.load(f)
                    
                    # Apply test type filter
                    tags = scenario_data.get('tags', {})
                    test_type = tags.get('type')
                    
                    if test_types_to_run and test_type not in test_types_to_run:
                        continue
                        
                    all_scenarios.append(scenario_data)
        
        return all_scenarios

    def get_suite_name(self) -> str:
        return self.suite_config.get('suite_name', 'Unknown Suite')
