> [!NOTE]  
> Very early work in progress, this is prompt engineernig based experiment


# Fantasy Football Analysis Platform

A self-hostable fantasy football analysis platform with FastAPI backend, SQLite database, and HTML frontend.

## Features

- **ESPN API Integration**: Fetch league data from ESPN fantasy football

That's it so far.
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

## Architecture

- FastAPI backend
- SQLite DB
- HTML/CSS frontend

## API Endpoints

- `GET /` - Serve frontend HTML
- `GET /health` - Health check
- `GET /api/teams` - Get all fantasy teams
- `GET /api/players` - Get all players

## Vibe Coding Diary
### 8/2/2025
I used cursor for the first time. In some ways it was neat, using their free pro trial. Was frustrating at times because it was trying to do WAY too much at once, and then sometimes it would hang when trying to use the CLI in a way that made me lose focus.

I've mostly used vscode agent mode so far, and tbh I like that better at this point in time. I'll give cursor one more night of usage probably, but if it doesn't get better I want to keep exploring other types.
 
### 8/6/2025

Cursor kept being annoying stalling on prompts, missing the point, etc. Was also more expensive than copilot, for less model options, and in my experience copilot agent actually works better. I looked into Windsail but decided not to, signed up for Kiro waitlist and maybe I'll try that. Anywho gonna try copilot from now on.
