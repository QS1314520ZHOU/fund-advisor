
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(os.getcwd())))
sys.path.insert(0, str(Path(os.getcwd()) / "backend"))

try:
    from backend.api import query
    print("Successfully imported query")
    for route in query.router.routes:
        print(f"Route: {route.path} | Name: {route.name} | Methods: {route.methods}")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
