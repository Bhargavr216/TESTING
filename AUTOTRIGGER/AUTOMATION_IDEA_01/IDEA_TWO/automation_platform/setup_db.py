import json
import os
import shutil
import psycopg2
from psycopg2 import sql

def create_database(db_name, user, password, host, port):
    conn = psycopg2.connect(
        dbname='postgres',
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.autocommit = True
    with conn.cursor() as cursor:
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    conn.close()
    print(f"Database {db_name} created successfully.")

def setup_fsm(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            DROP TABLE IF EXISTS fsm_job_queue CASCADE;
            DROP TABLE IF EXISTS fsm_job_queue_arch CASCADE;
            DROP TABLE IF EXISTS fsm_event_handled CASCADE;
            DROP TABLE IF EXISTS fsm_delivery_event CASCADE;
            DROP TABLE IF EXISTS fsm_audit CASCADE;

            CREATE TABLE fsm_job_queue (
                event_id VARCHAR(50) PRIMARY KEY,
                fulfilment_id VARCHAR(50),
                json_reponse JSONB,
                exception TEXT,
                operation VARCHAR(50),
                retry_count INT
            );
            CREATE TABLE fsm_job_queue_arch (
                event_id VARCHAR(50) PRIMARY KEY,
                fulfilment_id VARCHAR(50),
                json_reponse JSONB,
                exception TEXT,
                operation VARCHAR(50),
                retry_count INT
            );
            CREATE TABLE fsm_event_handled (
                event_id VARCHAR(50) PRIMARY KEY,
                processed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE fsm_delivery_event (
                fulfilment_id VARCHAR(50) PRIMARY KEY,
                order_id VARCHAR(50),
                POI_PAYLOAD JSONB,
                status VARCHAR(20)
            );
            CREATE TABLE fsm_audit (
                audit_id SERIAL PRIMARY KEY,
                event_id VARCHAR(50),
                event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exception TEXT,
                operation VARCHAR(50)
            );
        """)
    conn.commit()
    print("FSM tables recreated with new schema.")

def setup_mfs(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            DROP TABLE IF EXISTS mfs_event_handled CASCADE;
            DROP TABLE IF EXISTS mfs_job_queue CASCADE;
            DROP TABLE IF EXISTS mfs_audit CASCADE;

            CREATE TABLE mfs_event_handled (
                event_id VARCHAR(50) PRIMARY KEY,
                status VARCHAR(20)
            );
            CREATE TABLE mfs_job_queue (
                event_id VARCHAR(50) PRIMARY KEY,
                retry_count INT DEFAULT 0,
                state VARCHAR(20)
            );
            CREATE TABLE mfs_audit (
                audit_id SERIAL PRIMARY KEY,
                event_id VARCHAR(50),
                event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exception TEXT,
                operation VARCHAR(50)
            );
        """)
    conn.commit()
    print("MFS tables created.")

def setup_fos(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            DROP TABLE IF EXISTS fos_event_handled CASCADE;
            DROP TABLE IF EXISTS fos_job_queue CASCADE;
            DROP TABLE IF EXISTS fos_audit CASCADE;

            CREATE TABLE fos_event_handled (
                event_id VARCHAR(50) PRIMARY KEY,
                status VARCHAR(20)
            );
            CREATE TABLE fos_job_queue (
                event_id VARCHAR(50) PRIMARY KEY,
                retry_count INT DEFAULT 0,
                state VARCHAR(20)
            );
            CREATE TABLE fos_audit (
                audit_id SERIAL PRIMARY KEY,
                event_id VARCHAR(50),
                event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exception TEXT,
                operation VARCHAR(50)
            );
        """)
    conn.commit()
    print("FOS tables created.")

def generate_scenarios(service_name):
    scenarios = []
    base_path = f"scenarios/{service_name.lower()}"
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path, exist_ok=True)
    
    types = ["happy_path", "negative", "retry"]
    
    for test_type in types:
        scenario_no = f"{service_name}_{test_type.upper()}_001"
        lookup_key = f"{scenario_no.lower()}_event"
        
        event_payload = None
        look_up_ref = {}
        
        if service_name == "FSM":
            event_payload = [{"id": lookup_key, "data": {"ful_id": "ful_001"}}]
            look_up_ref = {"id": "event_id", "data.ful_id": "fulfilment_id"}

        scenario = {
            "scenario_no": scenario_no,
            "service": service_name,
            "tags": {"type": test_type, "priority": "high"},
            "lookup_key": lookup_key,
            "description": f"End-to-end {test_type} validation for {service_name}",
            "states": [
                {
                    "name": "EVENT_PROCESSED",
                    "event_payload": event_payload,
                    "look_up_ref": look_up_ref,
                    "rules": []
                }
            ]
        }
        
        # 1. Happy Path Rules
        if test_type == "happy_path":
            scenario["states"][0]["rules"].append({
                "type": "audit_validate",
                "validations": {
                    "count": 2,
                    "exact_sequence": [
                        {"operation": "CREATE", "exception": None},
                        {"operation": "PUBLISHED", "exception": None}
                    ]
                }
            })
            if service_name == "FSM":
                scenario["states"][0]["rules"].append({
                    "type": "smart_validate",
                    "validations": {
                        "fsm_job_queue_arch": {"operation": "PUBLISHED", "retry_count": 0}
                    }
                })
        
        # 2. Negative Rules
        elif test_type == "negative":
            scenario["states"][0]["rules"].append({
                "type": "audit_validate",
                "validations": {
                    "count": 1,
                    "exact_sequence": [
                        {"operation": "API_EXCEPTION", "exception": "!MANDATORY"}
                    ]
                }
            })
            
        # 3. Retry Rules
        elif test_type == "retry":
            scenario["states"][0]["rules"].append({
                "type": "audit_validate",
                "validations": {
                    "retry_attempts": 3,
                    "exact_sequence": [
                        {"operation": "CREATE", "exception": None},
                        {"operation": "VALIDATE", "exception": "!MANDATORY"},
                        {"operation": "VALIDATE", "exception": "!MANDATORY"},
                        {"operation": "VALIDATE", "exception": "!MANDATORY"},
                        {"operation": "VALIDATE", "exception": None}
                    ]
                }
            })

        file_path = os.path.join(base_path, f"{scenario_no.lower()}.json")
        with open(file_path, 'w') as f:
            json.dump(scenario, f, indent=2)
        scenarios.append(scenario)
    
    return scenarios

def seed_data(service_name, scenarios, conn):
    with conn.cursor() as cursor:
        for scenario in scenarios:
            unique_event_id = scenario["lookup_key"]
            test_type = scenario["tags"]["type"]
            audit_table = f"{service_name.lower()}_audit"
            
            if test_type == "happy_path":
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "CREATE", None))
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "PUBLISHED", None))
                if service_name == "FSM":
                    cursor.execute("INSERT INTO fsm_job_queue_arch (event_id, fulfilment_id, operation, retry_count) VALUES (%s, %s, %s, %s)", (unique_event_id, "ful_001", "PUBLISHED", 0))

            elif test_type == "negative":
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "API_EXCEPTION", "500 Error"))

            elif test_type == "retry":
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "CREATE", None))
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "VALIDATE", "Retry 1"))
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "VALIDATE", "Retry 2"))
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "VALIDATE", "Retry 3"))
                cursor.execute(f"INSERT INTO {audit_table} (event_id, operation, exception) VALUES (%s, %s, %s)", (unique_event_id, "VALIDATE", None))

    conn.commit()

def main():
    db_configs = {"FSM": "config/fsm_db.json", "MFS": "config/mfs_db.json", "FOS": "config/fos_db.json"}
    for service, config_path in db_configs.items():
        # Scenarios are only generated once per service
        scenarios = generate_scenarios(service)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        create_database(config['database'], config['user'], config['password'], config['host'], config['port'])
        
        conn = psycopg2.connect(
            dbname=config['database'],
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port']
        )
        
        if service == "FSM": setup_fsm(conn)
        elif service == "MFS": setup_mfs(conn)
        elif service == "FOS": setup_fos(conn)
        
        seed_data(service, scenarios, conn)
        conn.close()

if __name__ == "__main__":
    main()
