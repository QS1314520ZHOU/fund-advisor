
import sys
import os
import sqlite3
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def check_status():
    db_path = 'd:/fund-advisor/backend/data/fund_advisor.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== Snapshot Status ===")
        cursor.execute("SELECT id, snapshot_date, total_funds, qualified_funds, status FROM snapshots ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Date: {row[1]}, Total: {row[2]}, Qualified: {row[3]}, Status: {row[4]}")
            
        print("\n=== Fund Count ===")
        cursor.execute("SELECT count(*) FROM funds")
        count = cursor.fetchone()[0]
        print(f"Total Funds in 'funds' table: {count}")

        # Check update logs
        print("\n=== Recent Update Logs ===")
        # Correct column name: task_type
        cursor.execute("SELECT id, task_type, status, message, started_at, completed_at FROM update_logs ORDER BY id DESC LIMIT 5")
        logs = cursor.fetchall()
        for log in logs:
            print(f"ID: {log[0]}, Type: {log[1]}, Status: {log[2]}, Msg: {log[3]}")
            print(f"   Started: {log[4]}, Completed: {log[5]}")

        conn.close()
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_status()
