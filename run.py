"""Entry point for the Manual Production Order API.

Host/port/reload are read from the environment (.env). Run with:  uv run run.py
"""

import uvicorn

from backend.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
    )
