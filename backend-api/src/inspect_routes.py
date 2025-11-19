import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.resolve()
sys.path.insert(0, str(src_path))

try:
    from app.main import app
    
    # app is socketio.ASGIApp, need inner app
    if hasattr(app, 'other_asgi_app'):
        fastapi_app = app.other_asgi_app
        print("Found wrapped FastAPI app")
    else:
        fastapi_app = app
        print("Found FastAPI app directly")

    print("\nRegistered Routes:")
    for route in fastapi_app.routes:
        if hasattr(route, "path"):
            methods = ", ".join(route.methods) if hasattr(route, "methods") else "ANY"
            print(f"  {methods} {route.path}")
        else:
            print(f"  {route}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
