"""
FastAPI application for Fantasy Football Analysis
"""

import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import get_database_path, init_database
from .logging_config import get_logger

# Initialize FastAPI app
app = FastAPI(
    title="Fantasy Football Analysis",
    description="A comprehensive fantasy football analysis platform",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

# Get logger for this module
logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_database()
        logger.info(f"Database initialized at: {get_database_path()}")

        # Initialize ESPN data if database is empty
        from .database import execute_query

        teams_count = execute_query("SELECT COUNT(*) as count FROM fantasy_teams")
        if teams_count[0]["count"] == 0:
            logger.info("Database is empty, initializing ESPN data...")
            from .espn import init_espn_data

            success = init_espn_data()
            if success:
                logger.info("ESPN data initialization complete!")
            else:
                logger.warning("ESPN data initialization failed, falling back to sample data...")
                from .init_data import init_sample_data

                init_sample_data()
                logger.info("Sample data initialization complete!")
        else:
            logger.info("Database already contains data, skipping initialization.")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("app/frontend/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": get_database_path()}


@app.get("/api/teams")
async def get_teams():
    """Get all fantasy teams"""
    try:
        from .database import execute_query

        teams = execute_query("SELECT * FROM fantasy_teams ORDER BY team_name")
        return {"teams": [dict(team) for team in teams]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players")
async def get_players():
    """Get all players"""
    try:
        from .database import execute_query

        players = execute_query("SELECT * FROM players ORDER BY name")
        return {"players": [dict(player) for player in players]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
