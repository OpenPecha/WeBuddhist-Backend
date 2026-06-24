import os

# Keep the shared FastAPI app importable in tests without enforcing production limits.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
