"""
Threat Watch FastAPI application factory
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from tools.threat_watch import __version__
from tools.threat_watch.routers import events, config, webhooks
from tools.threat_watch.database import ThreatEvent
from tools.threat_watch.models import SystemStatus
from tools.threat_watch.scheduler import get_last_refresh, DEFAULT_REFRESH_INTERVAL
from shared.database import get_db_session

# Get the directory containing this file
BASE_DIR = Path(__file__).parent

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app() -> FastAPI:
    """
    Create and configure the Threat Watch sub-application

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Threat Watch",
        version=__version__,
        description="IDS/IPS monitoring and threat analysis for UniFi networks"
    )

    # Mount static files
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="threats_static"
    )

    # Include API routers
    app.include_router(events.router)
    app.include_router(config.router)
    app.include_router(webhooks.router)

    # Dashboard route
    @app.get("/")
    async def dashboard(request: Request):
        """Serve the Threat Watch dashboard"""
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )

    # Status endpoint
    @app.get("/api/status", response_model=SystemStatus, tags=["status"])
    async def get_status(
        db: AsyncSession = Depends(get_db_session)
    ):
        """
        Get system status including last refresh time and event counts
        """
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)

        # Get total event count
        total_result = await db.execute(select(func.count(ThreatEvent.id)))
        total_events = total_result.scalar() or 0

        # Get events in last 24 hours
        result_24h = await db.execute(
            select(func.count(ThreatEvent.id)).where(ThreatEvent.timestamp >= day_ago)
        )
        events_24h = result_24h.scalar() or 0

        return SystemStatus(
            last_refresh=get_last_refresh(),
            total_events=total_events,
            events_24h=events_24h,
            refresh_interval_seconds=DEFAULT_REFRESH_INTERVAL
        )

    return app
