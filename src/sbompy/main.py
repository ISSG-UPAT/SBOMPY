"""
Entrypoint for running SBOMPY as an application.

Example:
  sbompy
or:
  python -m sbompy.main
"""

from __future__ import annotations

import os
import uvicorn

from .api import app


def run() -> None:
    """Run the API server via uvicorn."""
    host = os.getenv("SBOMPY_HOST", "0.0.0.0")
    port = int(os.getenv("SBOMPY_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
