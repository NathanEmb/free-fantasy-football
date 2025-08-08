"""
FastAPI application for Fantasy Football Analysis
"""

import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.database import get_database_path, init_database
from src.logging_config import get_logger

# Initialize FastAPI app
app = FastAPI(
    title="Fantasy Football Analysis",
    description="A comprehensive fantasy football analysis platform",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get logger for this module
logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_database()
        logger.info(f"Database initialized at: {get_database_path()}")

        # Initialize ESPN data if database is empty
        from src.database import execute_query

        teams_count = execute_query("SELECT COUNT(*) as count FROM fantasy_teams")
        if teams_count[0]["count"] == 0:
            logger.info("Database is empty, initializing ESPN data...")
            from src.espn import init_espn_data

            success = init_espn_data()
            if success:
                logger.info("ESPN data initialization complete!")
            else:
                logger.warning("ESPN data initialization failed, falling back to sample data...")
                from src.init_data import init_sample_data

                init_sample_data()
                logger.info("Sample data initialization complete!")
        else:
            logger.info("Database already contains data, skipping initialization.")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": get_database_path()}


@app.get("/api/teams")
async def get_teams():
    """Get all fantasy teams"""
    try:
        from src.database import execute_query

        teams = execute_query("SELECT * FROM fantasy_teams ORDER BY team_name")
        return {"teams": [dict(team) for team in teams]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players")
async def get_players():
    """Get all players"""
    try:
        from src.database import execute_query

        players = execute_query("SELECT * FROM players ORDER BY name")
        return {"players": [dict(player) for player in players]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams-with-players")
async def get_teams_with_players():
    """Get all teams with their roster of players and stats"""
    try:
        from src.database import execute_query

        # Get all teams
        teams = execute_query("SELECT * FROM fantasy_teams ORDER BY points_for DESC")

        teams_with_players = []
        for team in teams:
            team_dict = dict(team)

            # Get players for this team from roster_entries
            # First check if roster_entries has data
            try:
                players_query = """
                SELECT p.*, re.is_starting, re.acquisition_type, re.acquired_date,
                       nt.team_name as nfl_team_name, nt.team_code as nfl_team_code
                FROM players p
                LEFT JOIN roster_entries re ON p.id = re.player_id
                LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
                WHERE re.fantasy_team_id = ?
                ORDER BY 
                    CASE p.position 
                        WHEN 'QB' THEN 1 
                        WHEN 'RB' THEN 2 
                        WHEN 'WR' THEN 3 
                        WHEN 'TE' THEN 4 
                        WHEN 'K' THEN 5 
                        WHEN 'DEF' THEN 6 
                        ELSE 7 
                    END,
                    re.is_starting DESC,
                    p.name
                """
                players = execute_query(players_query, (team["id"],))
                team_dict["players"] = [dict(player) for player in players]
                team_dict["player_count"] = len(players)

                # Calculate roster composition
                positions = {}
                for player in players:
                    pos = player["position"]
                    positions[pos] = positions.get(pos, 0) + 1
                team_dict["roster_composition"] = positions

            except Exception as e:
                # If roster_entries doesn't exist or has issues, just return empty roster
                logger.warning(f"Could not load roster for team {team['id']}: {e}")
                team_dict["players"] = []
                team_dict["player_count"] = 0
                team_dict["roster_composition"] = {}

            teams_with_players.append(team_dict)

        return {"teams": teams_with_players}
    except Exception as e:
        logger.error(f"Error in get_teams_with_players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
