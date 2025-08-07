# Free Fantasy Football Platform - AI Coding Instructions

## Architecture Overview
This is a self-hostable fantasy football dashboard with **FastAPI + SQLite + HTML frontend**. The core architecture uses an **adapter pattern** where external fantasy platforms (ESPN) are integrated through adapters that convert their data into our unified core data model.

**Key Components:**
- `app/backend/src/models.py` - Core data models (Player, FantasyTeam, LeagueConfig, etc.)
- `app/backend/src/espn.py` - ESPN API adapter with conversion functions
- `app/backend/src/database.py` - SQLite database utilities with context managers
- `app/backend/src/main.py` - FastAPI application entry point
- `app/database/schema.sql` - Complete database schema

## Development Workflow

**Essential Commands:**
- `uv run python -m app.backend.src.main` - Run FastAPI server
- `uv run pytest app/backend/test/` - Run all tests
- `uv sync` - Install/sync dependencies
- Always run pytest after Python changes

**Testing Pattern:**
- Tests are in `app/backend/test/` with comprehensive integration tests
- Use `temp_database` fixture for database testing
- Mock ESPN API calls using `unittest.mock`
- Change to `app/backend/` directory when running tests

## Critical Project Patterns

**Adapter Pattern Implementation:**
```python
# ESPN data -> Core models -> SQLite
espn_league = ESPNLeague(league_id, year)
teams = convert_teams(espn_league)  # ESPN -> FantasyTeam models
players = convert_players(espn_league)  # ESPN -> Player models
```

**Database Operations:**
```python
from .database import get_db_connection
with get_db_connection() as conn:
    conn.execute("INSERT INTO players...", values)
    conn.commit()
```

**Model Architecture:**
- All models use `dataclasses` with UUIDs for primary keys
- Enums for constrained values (Position, Platform, ScoringType)
- Models are platform-agnostic (ESPN-specific data converted via adapters)

## Environment & Dependencies

**Required Environment Variables:**
- `ESPN_LEAGUE_ID` - ESPN fantasy league ID (default: 24481082)
- `ESPN_YEAR` - Fantasy season year (default: 2024)
- `SQLITE_DB_PATH` - Database path (default: data/fantasy_football.db)

**Key Dependencies:**
- `espn-api` - ESPN fantasy football API client
- `fastapi[all]` - Web framework with uvicorn
- `sqlite3` - Database (built-in Python)

## Code Quality Standards

**Import Style:** Always use absolute imports (`from .database import...`)
**Type Hints:** Required for all functions and methods
**Logging:** Use `from .logging_config import get_logger` - never print statements
**Error Handling:** Use custom exceptions like `ESPNFantasyError`
**Testing:** Comprehensive test coverage with integration tests

## Data Flow Patterns

1. **Initialization:** `main.py` -> `init_espn_data()` -> ESPN API -> Core models -> SQLite
2. **API Requests:** FastAPI routes -> `database.execute_query()` -> SQLite -> JSON response
3. **Data Conversion:** ESPN objects -> `convert_*()` functions -> Core models -> Database insertion

## Docker & Deployment

**Container Structure:**
- Uses Python 3.13 slim image with uv package manager
- SQLite database persisted in `/app/data/` volume
- Exposes port 8000 for FastAPI application
- `start.sh` script handles database initialization
