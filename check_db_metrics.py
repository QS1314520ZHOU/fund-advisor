
import sqlite3
import json
import os

db_path = "d:/fund-advisor/data/fund_advisor.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get latest snapshot id
    cursor.execute("SELECT id, snapshot_date FROM snapshots ORDER BY id DESC LIMIT 1")
    snapshot = cursor.fetchone()
    if not snapshot:
        print("No snapshots found.")
    else:
        sid, sdate = snapshot
        print(f"Latest Snapshot: ID={sid}, Date={sdate}")
        
        # Check metrics
        cursor.execute(f"SELECT code, name, return_1d, latest_nav FROM fund_metrics WHERE snapshot_id={sid} LIMIT 10")
        rows = cursor.fetchall()
        print("\nTop 10 Fund Metrics:")
        print(f"{'Code':<10} {'Name':<20} {'Return_1d':<10} {'NAV':<10}")
        print("-" * 60)
        for row in rows:
            code, name, ret, nav = row
            print(f"{str(code):<10} {str(name):<20} {str(ret):<10} {str(nav):<10}")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
