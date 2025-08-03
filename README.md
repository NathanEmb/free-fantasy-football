# Fantasy Football Analysis Platform

A self-hostable fantasy football analysis platform with FastAPI backend, SQLite database, and HTML frontend.

## Features

- **ESPN API Integration**: Fetch league data from ESPN fantasy football
- **Comprehensive Data Model**: Players, teams, matchups, statistics, and more
- **Trade Analysis**: Analyze potential trades and their impact
- **Free Agent Recommendations**: Get recommendations for waiver pickups
- **Player Projections**: Store and analyze player projections
- **Single Container**: Everything runs in one Docker container

## Quick Start

### Using Docker

1. **Build and run the container:**
   ```bash
   docker build -t fantasy-football .
   docker run -p 8000:8000 fantasy-football
   ```

2. **Access the application:**
   - Frontend: http://localhost:8000
   - API: http://localhost:8000/api
   - Health Check: http://localhost:8000/health

### Development Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Run the application:**
   ```bash
   uv run src/backend/main.py
   ```

3. **Test the ESPN adapter:**
   ```bash
   uv run src/backend/espn_adapter.py
   ```

## Architecture

### Backend (FastAPI)
- **Location**: `src/backend/`
- **Main App**: `main.py`
- **Database**: `database.py` (SQLite)
- **ESPN Adapter**: `espn_adapter.py`
- **Models**: `models.py`

### Frontend (HTML/CSS/JavaScript)
- **Location**: `src/frontend/`
- **Main Page**: `index.html`

### Database (SQLite)
- **Schema**: `database/schema.sql`
- **Data Location**: `/app/data/fantasy_football.db` (in container)

## API Endpoints

- `GET /` - Serve frontend HTML
- `GET /health` - Health check
- `GET /api/teams` - Get all fantasy teams
- `GET /api/players` - Get all players

## Database Schema

The application uses SQLite with the following main tables:

- **nfl_teams** - NFL team information
- **players** - Player data and statistics
- **fantasy_teams** - Fantasy league teams
- **roster_entries** - Player roster assignments
- **fantasy_matchups** - Weekly matchups
- **player_game_stats** - Individual game statistics
- **trade_proposals** - Trade analysis
- **player_projections** - Player projections and rankings

## Configuration

### Environment Variables

- `SQLITE_DB_PATH` - Path to SQLite database file (default: `/app/data/fantasy_football.db`)

### ESPN API Configuration

Update the league ID and year in `src/backend/espn_adapter.py`:

```python
league_id = 24481082  # Your ESPN league ID
year = 2024           # Season year
```

## Development

### Project Structure

```
├── src/
│   ├── backend/
│   │   ├── main.py           # FastAPI application
│   │   ├── database.py       # Database utilities
│   │   ├── espn_adapter.py   # ESPN API integration
│   │   └── models.py         # Data models
│   ├── frontend/
│   │   └── index.html        # Web interface
│   └── database/
│       └── schema.sql        # Database schema
├── database/
│   └── schema.sql            # SQLite schema
├── docker/
│   └── start.sh             # Startup script
├── Dockerfile               # Container definition
└── pyproject.toml          # Python dependencies
```

### Adding New Features

1. **New API Endpoints**: Add to `src/backend/main.py`
2. **Database Operations**: Use functions in `src/backend/database.py`
3. **Data Models**: Update `src/backend/models.py`
4. **Frontend**: Modify `src/frontend/index.html`

## Data Import

The ESPN adapter can fetch league data:

```python
from src.backend.espn_adapter import get_league_data

league_config, teams, players, rosters, matchups = get_league_data(league_id, year)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `uv run src/backend/main.py`
5. Submit a pull request

## License

This project is open source and available under the MIT License.