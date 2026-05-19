import pyodbc
import json
import logging

class DBFactory:
    _connections = {}

    @staticmethod
    def get_connection(service_name: str, config: dict):
        if service_name not in DBFactory._connections:
            try:
                # Use Azure Connection String if available
                conn_str = config.get('connection_string')
                if conn_str:
                    conn = pyodbc.connect(conn_str)
                    DBFactory._connections[service_name] = conn
                    logging.info(f"Connected to Azure DB for {service_name}")
                else:
                    # Fallback to standard psycopg2 for local dev
                    import psycopg2
                    conn = psycopg2.connect(
                        dbname=config['database'],
                        user=config.get('user'),
                        password=config.get('password'),
                        host=config.get('host'),
                        port=config.get('port')
                    )
                    DBFactory._connections[service_name] = conn
            except Exception as e:
                logging.error(f"Error connecting to DB for {service_name}: {e}")
                return None
        return DBFactory._connections[service_name]

    @staticmethod
    def close_connection(service_name: str):
        if service_name in DBFactory._connections:
            conn = DBFactory._connections.pop(service_name)
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def close_all():
        for service_name in list(DBFactory._connections.keys()):
            DBFactory.close_connection(service_name)
