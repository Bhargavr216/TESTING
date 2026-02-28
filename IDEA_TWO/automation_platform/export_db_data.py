import json
import psycopg2
from datetime import datetime
from decimal import Decimal

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, Decimal):
        return float(x)
    raise TypeError("Unknown type")

def get_db_data(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    conn = psycopg2.connect(
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['user'],
        password=config['password']
    )
    
    db_data = {}
    with conn.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            table_rows = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                table_rows.append(row_dict)
            
            db_data[table] = table_rows
            
    conn.close()
    return db_data

def main():
    services = {
        "FSM": "config/fsm_db.json",
        "MFS": "config/mfs_db.json",
        "FOS": "config/fos_db.json"
    }
    
    full_dump = {}
    
    for service, config in services.items():
        print(f"Exporting data for {service}...")
        try:
            full_dump[service] = get_db_data(config)
        except Exception as e:
            print(f"Error exporting {service}: {e}")
            full_dump[service] = {"error": str(e)}
            
    with open('db_dump.json', 'w') as f:
        json.dump(full_dump, f, indent=2, default=datetime_handler)
        
    print("\nExport complete! Data saved to 'db_dump.json'.")

if __name__ == "__main__":
    main()
