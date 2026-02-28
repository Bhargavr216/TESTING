import json
import os
import psycopg2
from typing import Dict, Any

class DatabaseFactory:
    _connections: Dict[str, Any] = {}

    @staticmethod
    def get_connection(service_name: str, db_config_path: str):
        """
        Dynamically loads DB config and opens a connection for the given service.
        """
        if service_name in DatabaseFactory._connections:
            # Check if connection is still alive
            try:
                with DatabaseFactory._connections[service_name].cursor() as cursor:
                    cursor.execute("SELECT 1")
                return DatabaseFactory._connections[service_name]
            except Exception:
                # Reconnect if connection is dead
                DatabaseFactory.close_connection(service_name)

        # Load config
        if not os.path.isabs(db_config_path):
            # Assume path relative to the automation_platform root
            # This is a bit tricky, let's try to resolve it relative to the current working directory or a known base
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_config_path = os.path.join(base_path, db_config_path)

        with open(db_config_path, 'r') as f:
            config = json.load(f)

        try:
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password']
            )
            DatabaseFactory._connections[service_name] = conn
            return conn
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database for {service_name}: {e}")

    @staticmethod
    def close_connection(service_name: str):
        if service_name in DatabaseFactory._connections:
            conn = DatabaseFactory._connections.pop(service_name)
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def close_all():
        for service_name in list(DatabaseFactory._connections.keys()):
            DatabaseFactory.close_connection(service_name)
