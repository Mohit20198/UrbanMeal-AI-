import os
import sys
import redshift_connector
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("REDSHIFT_HOST")
PORT = int(os.getenv("REDSHIFT_PORT", "5439"))
DATABASE = os.getenv("REDSHIFT_DATABASE", "dev")
USER = os.getenv("REDSHIFT_USER")
PASSWORD = os.getenv("REDSHIFT_PASSWORD")

def run():
    if not HOST or not USER or not PASSWORD:
        print("\n[!] Missing Redshift connection details.")
        print("Please set them in your environment or provide them:")
        host = input("Redshift Host/Endpoint: ").strip() or HOST
        user = input("Redshift User: ").strip() or USER
        password = input("Redshift Password: ").strip() or PASSWORD
        database = input("Redshift Database [dev]: ").strip() or DATABASE
    else:
        host, user, password, database = HOST, USER, PASSWORD, DATABASE

    print(f"\nConnecting to Amazon Redshift at {host}:{PORT}/{database} as {user}...")
    try:
        conn = redshift_connector.connect(
            host=host,
            port=PORT,
            database=database,
            user=user,
            password=password,
            ssl=True
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("Connected successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Redshift: {e}")
        sys.exit(1)

    sql_path = os.path.join(os.path.dirname(__file__), "run_all.sql")
    print(f"\nReading {sql_path}...")
    with open(sql_path, "r", encoding="utf-8") as f:
        full_sql = f.read()

    # Split on semicolon, ignoring comment lines
    raw_statements = full_sql.split(";")
    for stmt in raw_statements:
        clean_stmt = stmt.strip()
        # Filter out empty or pure-comment statements
        lines = [line.strip() for line in clean_stmt.splitlines() if line.strip() and not line.strip().startswith("--")]
        if not lines:
            continue
        exec_stmt = "\n".join(lines)
        first_line = lines[0][:60]
        print(f"Executing: {first_line}...")
        try:
            cursor.execute(exec_stmt)
            if "SELECT" in exec_stmt.upper() and "count(*)" in exec_stmt.lower():
                results = cursor.fetchall()
                print("\n=== Row Counts in RAW ===")
                for r in results:
                    print(f"  {r[0]:<15}: {r[1]:>10} rows")
                print("==========================\n")
        except Exception as e:
            print(f"[ERROR] Statement failed: {e}\nQuery was:\n{exec_stmt}\n")

    cursor.close()
    conn.close()
    print("\nAll Redshift setup and COPY commands completed!")

if __name__ == "__main__":
    run()
