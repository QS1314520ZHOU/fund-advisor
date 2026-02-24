from backend.main import app
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"{route.path} - {getattr(route, 'methods', 'NA')}")
