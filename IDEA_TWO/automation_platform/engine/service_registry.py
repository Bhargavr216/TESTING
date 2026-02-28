import json
import os
from typing import Dict, Any, Optional

class ServiceRegistry:
    _services: Dict[str, Any] = {}

    @classmethod
    def load(cls, config_path: str = None):
        """
        Loads the service configuration.
        """
        if config_path is None:
            # Assume default path
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_path, 'config', 'services.json')

        with open(config_path, 'r') as f:
            data = json.load(f)
            cls._services = data.get('services', {})

    @classmethod
    def get_service(cls, service_name: str) -> Optional[Dict[str, Any]]:
        return cls._services.get(service_name)

    @classmethod
    def get_db_config_path(cls, service_name: str) -> Optional[str]:
        service = cls.get_service(service_name)
        return service.get('db_config') if service else None

    @classmethod
    def get_scenario_path(cls, service_name: str) -> Optional[str]:
        service = cls.get_service(service_name)
        return service.get('scenario_path') if service else None

    @classmethod
    def list_services(cls):
        return list(cls._services.keys())
