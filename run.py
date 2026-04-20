"""
run.py — Convenience launcher.

Usage:
    python run.py              # default: 0.0.0.0:8000, auto-reload off
    python run.py --reload     # enable hot-reload for development
    python run.py --port 9000
"""

import argparse
import uvicorn
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Start Orbital Insight AI server")
    parser.add_argument("--host",   default=settings.HOST,  help="Bind host")
    parser.add_argument("--port",   default=settings.PORT,  type=int, help="Bind port")
    parser.add_argument("--reload", action="store_true",    help="Enable hot-reload")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
