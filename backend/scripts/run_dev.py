"""Local development server launcher.

Starts FastAPI with uvicorn on localhost:8000.
For development without Docker — just run:
    python scripts/run_dev.py
"""

import os
import sys


# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    """Start the development server."""
    # Set development defaults if not in env
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")

    # Default to SQLite for quick local dev if no PostgreSQL configured
    if not os.environ.get("DATABASE_URL"):
        db_url = "sqlite+aiosqlite:///./dev.db"
        os.environ["DATABASE_URL"] = db_url
        print(f"  Database: {db_url} (SQLite for local dev)")
        print("  Set DATABASE_URL env var for PostgreSQL")
    else:
        print(f"  Database: {os.environ['DATABASE_URL'][:50]}...")

    import uvicorn

    print("=" * 50)
    print("  Smart Price API — Development Server")
    print("=" * 50)
    print("  API:  http://127.0.0.1:8000")
    print("  Docs: http://127.0.0.1:8000/docs")
    print("  Redoc: http://127.0.0.1:8000/redoc")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    main()
