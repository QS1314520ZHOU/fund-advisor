
import sys
import os
import logging
import traceback

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_diagnostic():
    try:
        print("Importing modules...")
        from backend.services.snapshot import SnapshotService
        from backend.database import get_db
        
        db = get_db()
        print(f"DB Path: {db.db_path}")
        
        # Check current snapshot count
        with db.get_cursor() as cursor:
            cursor.execute("SELECT count(*) FROM snapshots")
            print(f"Snapshot count before: {cursor.fetchone()[0]}")
            
        print("Initializing SnapshotService...")
        service = SnapshotService()
        
        print("Starting create_full_snapshot(skip_filter=True)...")
        # Define a callback to print progress
        def progress_callback(step, current, total, message):
            print(f"PROGRESS: [{step}] {current}/{total} - {message}")
            
        # Hook into the service's progress method if possible, or just rely on its logging
        # We can mock the fetcher to avoid fetching EVERYTHING if we just want to test logic, 
        # but here we want to run the REAL update.
        
        # We'll just run it. It logs to stdout/stderr which we capture.
        result = service.create_full_snapshot(skip_filter=True)
        print(f"Result: {result}")
        
        # Check snapshot count after
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                print(f"Latest Snapshot: ID={row['id']}, Date={row['snapshot_date']}, Status={row['status']}")
                
    except Exception as e:
        print("EXCEPTION OCCURRED:")
        traceback.print_exc()

if __name__ == "__main__":
    run_diagnostic()
