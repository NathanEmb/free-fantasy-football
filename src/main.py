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
                logger.error("ESPN data initialization failed. Please check your ESPN_LEAGUE_ID and ESPN_YEAR environment variables.")
                raise Exception("Failed to initialize ESPN data - no fallback available")
        else:
            logger.info("Database already contains data, skipping initialization.")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


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


# ============================================================================
# TEAM MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/teams/standings")
async def get_league_standings():
    """Get current league standings with advanced metrics"""
    try:
        from src.database import execute_query

        # Get all teams with calculated metrics
        teams = execute_query("SELECT * FROM fantasy_teams")
        
        standings = []
        for team in teams:
            team_dict = dict(team)
            
            # Calculate derived metrics
            total_games = team_dict["wins"] + team_dict["losses"] + team_dict["ties"]
            team_dict["total_games"] = total_games
            team_dict["win_percentage"] = team_dict["wins"] / max(1, total_games) if total_games > 0 else 0.0
            team_dict["average_points_for"] = team_dict["points_for"] / max(1, total_games) if total_games > 0 else 0.0
            team_dict["average_points_against"] = team_dict["points_against"] / max(1, total_games) if total_games > 0 else 0.0
            team_dict["point_differential"] = team_dict["points_for"] - team_dict["points_against"]
            
            standings.append(team_dict)
        
        # Sort by wins first, then by points for
        standings.sort(key=lambda x: (x["wins"], x["points_for"]), reverse=True)
        
        # Add ranking
        for i, team in enumerate(standings):
            team["rank"] = i + 1
        
        return {"standings": standings}
    except Exception as e:
        logger.error(f"Error getting league standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_id}")
async def get_team_details(team_id: str):
    """Get detailed information for a specific team"""
    try:
        from src.database import execute_query

        # Get team basic info
        teams = execute_query("SELECT * FROM fantasy_teams WHERE id = ?", (team_id,))
        if not teams:
            raise HTTPException(status_code=404, detail="Team not found")
        
        team = dict(teams[0])
        
        # Get roster with player details
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
        players = execute_query(players_query, (team_id,))
        team["roster"] = [dict(player) for player in players]
        
        # Calculate team metrics
        team["win_percentage"] = team["wins"] / max(1, team["wins"] + team["losses"] + team["ties"])
        team["average_points_for"] = team["points_for"] / max(1, team["wins"] + team["losses"] + team["ties"])
        team["average_points_against"] = team["points_against"] / max(1, team["wins"] + team["losses"] + team["ties"])
        team["point_differential"] = team["points_for"] - team["points_against"]
        
        return {"team": team}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team details for {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_id}/roster")
async def get_team_roster(team_id: str):
    """Get detailed roster information for a team"""
    try:
        from src.database import execute_query

        # Verify team exists
        teams = execute_query("SELECT id FROM fantasy_teams WHERE id = ?", (team_id,))
        if not teams:
            raise HTTPException(status_code=404, detail="Team not found")

        # Get roster with comprehensive player info
        roster_query = """
        SELECT p.*, re.is_starting, re.acquisition_type, re.acquired_date,
               nt.team_name as nfl_team_name, nt.team_code as nfl_team_code,
               nt.conference, nt.division
        FROM players p
        LEFT JOIN roster_entries re ON p.id = re.player_id
        LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
        WHERE re.fantasy_team_id = ?
        ORDER BY 
            re.is_starting DESC,
            CASE p.position 
                WHEN 'QB' THEN 1 
                WHEN 'RB' THEN 2 
                WHEN 'WR' THEN 3 
                WHEN 'TE' THEN 4 
                WHEN 'K' THEN 5 
                WHEN 'DEF' THEN 6 
                ELSE 7 
            END,
            p.name
        """
        roster = execute_query(roster_query, (team_id,))
        
        # Organize roster by starting/bench
        starting_lineup = []
        bench = []
        position_counts = {}
        
        for player in roster:
            player_dict = dict(player)
            position = player_dict["position"]
            position_counts[position] = position_counts.get(position, 0) + 1
            
            if player_dict["is_starting"]:
                starting_lineup.append(player_dict)
            else:
                bench.append(player_dict)
        
        return {
            "team_id": team_id,
            "starting_lineup": starting_lineup,
            "bench": bench,
            "total_players": len(roster),
            "position_counts": position_counts,
            "roster_composition": {
                "starting_players": len(starting_lineup),
                "bench_players": len(bench)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting roster for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_id}/schedule")
async def get_team_schedule(team_id: str):
    """Get a team's fantasy matchup schedule"""
    try:
        from src.database import execute_query

        # Verify team exists
        teams = execute_query("SELECT id, team_name FROM fantasy_teams WHERE id = ?", (team_id,))
        if not teams:
            raise HTTPException(status_code=404, detail="Team not found")
        
        team_info = dict(teams[0])

        # Get team's matchups (both home and away)
        schedule_query = """
        SELECT m.*, 
               ht.team_name as home_team_name, ht.owner_name as home_owner_name,
               at.team_name as away_team_name, at.owner_name as away_owner_name
        FROM fantasy_matchups m
        LEFT JOIN fantasy_teams ht ON m.home_team_id = ht.id
        LEFT JOIN fantasy_teams at ON m.away_team_id = at.id
        WHERE m.home_team_id = ? OR m.away_team_id = ?
        ORDER BY m.week
        """
        matchups = execute_query(schedule_query, (team_id, team_id))
        
        schedule = []
        for matchup in matchups:
            matchup_dict = dict(matchup)
            
            # Determine if this team is home or away
            is_home = matchup_dict["home_team_id"] == team_id
            opponent_id = matchup_dict["away_team_id"] if is_home else matchup_dict["home_team_id"]
            opponent_name = matchup_dict["away_team_name"] if is_home else matchup_dict["home_team_name"]
            opponent_owner = matchup_dict["away_owner_name"] if is_home else matchup_dict["home_owner_name"]
            
            # Calculate result
            team_score = matchup_dict["home_score"] if is_home else matchup_dict["away_score"]
            opponent_score = matchup_dict["away_score"] if is_home else matchup_dict["home_score"]
            
            result = "TBD"
            if team_score > 0 or opponent_score > 0:  # Game has been played
                if team_score > opponent_score:
                    result = "W"
                elif team_score < opponent_score:
                    result = "L"
                else:
                    result = "T"
            
            schedule.append({
                "week": matchup_dict["week"],
                "is_home": is_home,
                "opponent_id": opponent_id,
                "opponent_name": opponent_name,
                "opponent_owner": opponent_owner,
                "team_score": team_score,
                "opponent_score": opponent_score,
                "result": result,
                "is_playoff": matchup_dict["is_playoff"],
                "matchup_id": matchup_dict["id"]
            })
        
        return {
            "team_id": team_id,
            "team_name": team_info["team_name"],
            "schedule": schedule
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_id}/stats")
async def get_team_stats(team_id: str):
    """Get comprehensive statistics for a team"""
    try:
        from src.database import execute_query

        # Verify team exists and get basic info
        teams = execute_query("SELECT * FROM fantasy_teams WHERE id = ?", (team_id,))
        if not teams:
            raise HTTPException(status_code=404, detail="Team not found")
        
        team = dict(teams[0])

        # Get weekly scores if available
        weekly_scores_query = """
        SELECT week, total_score, bench_score, optimal_score
        FROM fantasy_team_weekly_scores 
        WHERE fantasy_team_id = ?
        ORDER BY week
        """
        weekly_scores = execute_query(weekly_scores_query, (team_id,))
        
        # Calculate statistics
        total_games = team["wins"] + team["losses"] + team["ties"]
        stats = {
            "team_id": team_id,
            "team_name": team["team_name"],
            "owner_name": team["owner_name"],
            "record": {
                "wins": team["wins"],
                "losses": team["losses"], 
                "ties": team["ties"],
                "total_games": total_games,
                "win_percentage": team["wins"] / max(1, total_games) if total_games > 0 else 0.0
            },
            "scoring": {
                "points_for": team["points_for"],
                "points_against": team["points_against"],
                "point_differential": team["points_for"] - team["points_against"],
                "average_points_for": team["points_for"] / max(1, total_games) if total_games > 0 else 0.0,
                "average_points_against": team["points_against"] / max(1, total_games) if total_games > 0 else 0.0
            },
            "weekly_scores": [dict(score) for score in weekly_scores]
        }
        
        # Add weekly score statistics if available
        if weekly_scores:
            scores = [score["total_score"] for score in weekly_scores]
            stats["scoring"]["highest_week"] = max(scores)
            stats["scoring"]["lowest_week"] = min(scores)
            stats["scoring"]["score_variance"] = max(scores) - min(scores)
        
        return {"stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PLAYER ANALYSIS ENDPOINTS  
# ============================================================================

@app.get("/api/players/available")
async def get_available_players():
    """Get players who are not currently on any fantasy team roster"""
    try:
        from src.database import execute_query

        # Get players not in roster_entries
        available_query = """
        SELECT p.*, nt.team_name as nfl_team_name, nt.team_code as nfl_team_code
        FROM players p
        LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
        LEFT JOIN roster_entries re ON p.id = re.player_id
        WHERE re.player_id IS NULL AND p.is_active = 1
        ORDER BY p.position, p.name
        """
        players = execute_query(available_query)
        
        # Group by position
        available_by_position = {}
        for player in players:
            position = player["position"]
            if position not in available_by_position:
                available_by_position[position] = []
            available_by_position[position].append(dict(player))
        
        return {
            "available_players": [dict(player) for player in players],
            "available_by_position": available_by_position,
            "total_available": len(players)
        }
    except Exception as e:
        logger.error(f"Error getting available players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/rankings")
async def get_player_rankings(position: str = None, week: int = None):
    """Get player rankings, optionally filtered by position and/or week"""
    try:
        from src.database import execute_query

        # Build query based on filters
        query = """
        SELECT pr.*, p.name, p.position as player_position,
               nt.team_name as nfl_team_name, nt.team_code as nfl_team_code
        FROM player_rankings pr
        JOIN players p ON pr.player_id = p.id
        LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
        WHERE 1=1
        """
        params = []
        
        if position:
            query += " AND pr.position = ?"
            params.append(position)
        
        if week:
            query += " AND pr.week = ?"
            params.append(week)
        
        query += " ORDER BY pr.position, pr.rank"
        
        rankings = execute_query(query, params)
        
        # Group by position
        rankings_by_position = {}
        for ranking in rankings:
            pos = ranking["position"]
            if pos not in rankings_by_position:
                rankings_by_position[pos] = []
            rankings_by_position[pos].append(dict(ranking))
        
        return {
            "rankings": [dict(ranking) for ranking in rankings],
            "rankings_by_position": rankings_by_position,
            "filters": {"position": position, "week": week}
        }
    except Exception as e:
        logger.error(f"Error getting player rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/players/compare")
async def compare_players(player_ids: list[str]):
    """Compare multiple players with their stats and projections"""
    if not player_ids or len(player_ids) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 player IDs")
    
    try:
        from src.database import execute_query

        players_data = []
        for player_id in player_ids:
            # Get player details
            player_query = """
            SELECT p.*, nt.team_name as nfl_team_name, nt.team_code as nfl_team_code
            FROM players p
            LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
            WHERE p.id = ?
            """
            players = execute_query(player_query, (player_id,))
            if not players:
                continue
                
            player = dict(players[0])
            
            # Get recent projections
            projections_query = """
            SELECT * FROM player_projections 
            WHERE player_id = ? 
            ORDER BY week DESC, created_at DESC
            LIMIT 5
            """
            projections = execute_query(projections_query, (player_id,))
            player["recent_projections"] = [dict(proj) for proj in projections]
            
            # Get rankings
            rankings_query = """
            SELECT * FROM player_rankings 
            WHERE player_id = ?
            ORDER BY created_at DESC
            LIMIT 3
            """
            rankings = execute_query(rankings_query, (player_id,))
            player["rankings"] = [dict(rank) for rank in rankings]
            
            players_data.append(player)
        
        if len(players_data) < 2:
            raise HTTPException(status_code=400, detail="Could not find enough valid players to compare")
        
        return {
            "comparison": players_data,
            "comparison_summary": {
                "total_players": len(players_data),
                "positions": list(set(p["position"] for p in players_data)),
                "teams": list(set(p["nfl_team_name"] for p in players_data if p["nfl_team_name"]))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}")
async def get_player_details(player_id: str):
    """Get detailed information for a specific player"""
    try:
        from src.database import execute_query

        # Get player with NFL team info
        player_query = """
        SELECT p.*, nt.team_name as nfl_team_name, nt.team_code as nfl_team_code,
               nt.conference, nt.division
        FROM players p
        LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
        WHERE p.id = ?
        """
        players = execute_query(player_query, (player_id,))
        if not players:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player = dict(players[0])
        
        # Get fantasy team info if rostered
        roster_query = """
        SELECT ft.id as fantasy_team_id, ft.team_name, ft.owner_name,
               re.is_starting, re.acquisition_type, re.acquired_date
        FROM roster_entries re
        JOIN fantasy_teams ft ON re.fantasy_team_id = ft.id
        WHERE re.player_id = ?
        """
        roster_info = execute_query(roster_query, (player_id,))
        
        if roster_info:
            player["fantasy_team"] = dict(roster_info[0])
        else:
            player["fantasy_team"] = None
        
        return {"player": player}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player details for {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}/projections")
async def get_player_projections(player_id: str, week: int = None):
    """Get projections for a specific player"""
    try:
        from src.database import execute_query

        # Verify player exists
        players = execute_query("SELECT id, name FROM players WHERE id = ?", (player_id,))
        if not players:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_info = dict(players[0])

        # Get projections
        query = """
        SELECT * FROM player_projections 
        WHERE player_id = ?
        """
        params = [player_id]
        
        if week:
            query += " AND week = ?"
            params.append(week)
        
        query += " ORDER BY week DESC, created_at DESC"
        
        projections = execute_query(query, params)
        
        return {
            "player_id": player_id,
            "player_name": player_info["name"],
            "projections": [dict(proj) for proj in projections],
            "total_projections": len(projections)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting projections for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}/stats")
async def get_player_stats(player_id: str):
    """Get game statistics for a specific player"""
    try:
        from src.database import execute_query

        # Verify player exists
        players = execute_query("SELECT id, name, position FROM players WHERE id = ?", (player_id,))
        if not players:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_info = dict(players[0])

        # Get game statistics
        stats_query = """
        SELECT pgs.*, ng.week, ng.season_year, ng.game_date,
               ht.team_name as home_team, at.team_name as away_team
        FROM player_game_stats pgs
        JOIN nfl_games ng ON pgs.nfl_game_id = ng.id
        JOIN nfl_teams ht ON ng.home_team_id = ht.id
        JOIN nfl_teams at ON ng.away_team_id = at.id
        WHERE pgs.player_id = ?
        ORDER BY ng.season_year DESC, ng.week DESC
        """
        stats = execute_query(stats_query, (player_id,))
        
        # Calculate season totals and averages
        if stats:
            total_fantasy_points = sum(stat["fantasy_points"] for stat in stats)
            games_played = len(stats)
            avg_fantasy_points = total_fantasy_points / games_played if games_played > 0 else 0
        else:
            total_fantasy_points = 0
            games_played = 0
            avg_fantasy_points = 0
        
        return {
            "player_id": player_id,
            "player_name": player_info["name"],
            "position": player_info["position"],
            "game_stats": [dict(stat) for stat in stats],
            "season_summary": {
                "games_played": games_played,
                "total_fantasy_points": total_fantasy_points,
                "average_fantasy_points": avg_fantasy_points
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MATCHUP ANALYSIS ENDPOINTS
# ============================================================================

@app.get("/api/matchups")
async def get_all_matchups():
    """Get all fantasy matchups with team details"""
    try:
        from src.database import execute_query

        matchups_query = """
        SELECT m.*, 
               ht.team_name as home_team_name, ht.owner_name as home_owner_name,
               at.team_name as away_team_name, at.owner_name as away_owner_name
        FROM fantasy_matchups m
        LEFT JOIN fantasy_teams ht ON m.home_team_id = ht.id
        LEFT JOIN fantasy_teams at ON m.away_team_id = at.id
        ORDER BY m.week, m.created_at
        """
        matchups = execute_query(matchups_query)
        
        # Group by week
        matchups_by_week = {}
        for matchup in matchups:
            week = matchup["week"]
            if week not in matchups_by_week:
                matchups_by_week[week] = []
            matchups_by_week[week].append(dict(matchup))
        
        return {
            "matchups": [dict(matchup) for matchup in matchups],
            "matchups_by_week": matchups_by_week,
            "total_matchups": len(matchups)
        }
    except Exception as e:
        logger.error(f"Error getting all matchups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/matchups/week/{week}")
async def get_matchups_by_week(week: int):
    """Get all matchups for a specific week"""
    try:
        from src.database import execute_query

        matchups_query = """
        SELECT m.*, 
               ht.team_name as home_team_name, ht.owner_name as home_owner_name,
               at.team_name as away_team_name, at.owner_name as away_owner_name
        FROM fantasy_matchups m
        LEFT JOIN fantasy_teams ht ON m.home_team_id = ht.id
        LEFT JOIN fantasy_teams at ON m.away_team_id = at.id
        WHERE m.week = ?
        ORDER BY m.created_at
        """
        matchups = execute_query(matchups_query, (week,))
        
        return {
            "week": week,
            "matchups": [dict(matchup) for matchup in matchups],
            "total_matchups": len(matchups)
        }
    except Exception as e:
        logger.error(f"Error getting matchups for week {week}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/matchups/{matchup_id}")
async def get_matchup_details(matchup_id: str):
    """Get detailed analysis for a specific matchup"""
    try:
        from src.database import execute_query

        # Get matchup details
        matchup_query = """
        SELECT m.*, 
               ht.team_name as home_team_name, ht.owner_name as home_owner_name,
               at.team_name as away_team_name, at.owner_name as away_owner_name
        FROM fantasy_matchups m
        LEFT JOIN fantasy_teams ht ON m.home_team_id = ht.id
        LEFT JOIN fantasy_teams at ON m.away_team_id = at.id
        WHERE m.id = ?
        """
        matchups = execute_query(matchup_query, (matchup_id,))
        if not matchups:
            raise HTTPException(status_code=404, detail="Matchup not found")
        
        matchup = dict(matchups[0])
        
        # Get rosters for both teams
        home_roster_query = """
        SELECT p.*, re.is_starting, nt.team_name as nfl_team_name
        FROM players p
        JOIN roster_entries re ON p.id = re.player_id
        LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
        WHERE re.fantasy_team_id = ?
        ORDER BY re.is_starting DESC, p.position, p.name
        """
        
        away_roster_query = home_roster_query  # Same query structure
        
        home_roster = execute_query(home_roster_query, (matchup["home_team_id"],))
        away_roster = execute_query(away_roster_query, (matchup["away_team_id"],))
        
        matchup["home_roster"] = [dict(player) for player in home_roster]
        matchup["away_roster"] = [dict(player) for player in away_roster]
        
        return {"matchup": matchup}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matchup details for {matchup_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRADE ANALYSIS ENDPOINTS
# ============================================================================

@app.get("/api/trades/proposals")
async def get_trade_proposals():
    """Get all trade proposals with details"""
    try:
        from src.database import execute_query

        # Get all trade proposals
        proposals_query = """
        SELECT tp.*, 
               pt.team_name as proposing_team_name, pt.owner_name as proposing_owner,
               rt.team_name as receiving_team_name, rt.owner_name as receiving_owner
        FROM trade_proposals tp
        LEFT JOIN fantasy_teams pt ON tp.proposing_team_id = pt.id
        LEFT JOIN fantasy_teams rt ON tp.receiving_team_id = rt.id
        ORDER BY tp.proposed_date DESC
        """
        proposals = execute_query(proposals_query)
        
        # Get trade items for each proposal
        for proposal in proposals:
            proposal_dict = dict(proposal)
            proposal_id = proposal_dict["id"]
            
            # Get trade items
            items_query = """
            SELECT ti.*, p.name as player_name, p.position,
                   ft.team_name as team_name
            FROM trade_items ti
            LEFT JOIN players p ON ti.player_id = p.id
            LEFT JOIN fantasy_teams ft ON ti.team_id = ft.id
            WHERE ti.trade_proposal_id = ?
            """
            items = execute_query(items_query, (proposal_id,))
            proposal_dict["trade_items"] = [dict(item) for item in items]
            
            # Get trade analysis if available
            analysis_query = """
            SELECT * FROM trade_analysis WHERE trade_proposal_id = ?
            """
            analysis = execute_query(analysis_query, (proposal_id,))
            proposal_dict["analysis"] = dict(analysis[0]) if analysis else None
        
        return {
            "proposals": [dict(proposal) for proposal in proposals],
            "total_proposals": len(proposals)
        }
    except Exception as e:
        logger.error(f"Error getting trade proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trades/proposals")
async def create_trade_proposal(
    proposing_team_id: str,
    receiving_team_id: str, 
    proposing_players: list[str] = [],
    receiving_players: list[str] = [],
    notes: str = None
):
    """Create a new trade proposal"""
    try:
        from src.database import execute_query, get_db_connection
        import uuid
        from datetime import datetime

        # Validate teams exist
        teams_query = "SELECT id FROM fantasy_teams WHERE id IN (?, ?)"
        teams = execute_query(teams_query, (proposing_team_id, receiving_team_id))
        if len(teams) != 2:
            raise HTTPException(status_code=400, detail="Invalid team IDs")

        # Validate players exist and belong to correct teams
        if proposing_players:
            prop_players_query = """
            SELECT COUNT(*) as count FROM roster_entries re
            WHERE re.player_id IN ({}) AND re.fantasy_team_id = ?
            """.format(','.join(['?' for _ in proposing_players]))
            params = proposing_players + [proposing_team_id]
            prop_count = execute_query(prop_players_query, params)
            if prop_count[0]["count"] != len(proposing_players):
                raise HTTPException(status_code=400, detail="Some proposing players don't belong to proposing team")

        if receiving_players:
            rec_players_query = """
            SELECT COUNT(*) as count FROM roster_entries re
            WHERE re.player_id IN ({}) AND re.fantasy_team_id = ?
            """.format(','.join(['?' for _ in receiving_players]))
            params = receiving_players + [receiving_team_id]
            rec_count = execute_query(rec_players_query, params)
            if rec_count[0]["count"] != len(receiving_players):
                raise HTTPException(status_code=400, detail="Some receiving players don't belong to receiving team")

        # Create trade proposal
        proposal_id = str(uuid.uuid4())
        with get_db_connection() as conn:
            # Insert trade proposal
            conn.execute("""
                INSERT INTO trade_proposals 
                (id, proposing_team_id, receiving_team_id, notes, proposed_date)
                VALUES (?, ?, ?, ?, ?)
            """, (proposal_id, proposing_team_id, receiving_team_id, notes, datetime.now().isoformat()))
            
            # Insert proposing team's players
            for player_id in proposing_players:
                conn.execute("""
                    INSERT INTO trade_items (id, trade_proposal_id, team_id, player_id)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), proposal_id, proposing_team_id, player_id))
            
            # Insert receiving team's players
            for player_id in receiving_players:
                conn.execute("""
                    INSERT INTO trade_items (id, trade_proposal_id, team_id, player_id)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), proposal_id, receiving_team_id, player_id))
            
            conn.commit()

        return {
            "proposal_id": proposal_id,
            "status": "created",
            "message": "Trade proposal created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trade proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trades/analyze")
async def analyze_trade(
    proposing_team_id: str,
    receiving_team_id: str,
    proposing_players: list[str] = [],
    receiving_players: list[str] = []
):
    """Analyze a potential trade between two teams"""
    try:
        from src.database import execute_query

        # Get team information
        teams_query = "SELECT * FROM fantasy_teams WHERE id IN (?, ?)"
        teams = execute_query(teams_query, (proposing_team_id, receiving_team_id))
        if len(teams) != 2:
            raise HTTPException(status_code=400, detail="Invalid team IDs")
        
        # Get player details for analysis
        all_players = proposing_players + receiving_players
        if all_players:
            players_query = """
            SELECT p.*, pr.rank, pr.tier
            FROM players p
            LEFT JOIN player_rankings pr ON p.id = pr.player_id
            WHERE p.id IN ({})
            """.format(','.join(['?' for _ in all_players]))
            players = execute_query(players_query, all_players)
        else:
            players = []

        # Simple trade value calculation (this could be much more sophisticated)
        proposing_value = 0
        receiving_value = 0
        
        for player in players:
            player_dict = dict(player)
            # Use inverse of ranking as simple value metric (lower rank = higher value)
            base_value = max(0, 200 - (player_dict.get("rank", 100)))
            
            if player_dict["id"] in proposing_players:
                proposing_value += base_value
            else:
                receiving_value += base_value
        
        # Calculate trade balance
        value_difference = abs(proposing_value - receiving_value)
        trade_balance = "Balanced" if value_difference <= 20 else "Unbalanced"
        
        analysis = {
            "proposing_team_value": proposing_value,
            "receiving_team_value": receiving_value,
            "value_difference": value_difference,
            "trade_balance": trade_balance,
            "proposing_players_details": [dict(p) for p in players if p["id"] in proposing_players],
            "receiving_players_details": [dict(p) for p in players if p["id"] in receiving_players],
            "recommendation": "Accept" if trade_balance == "Balanced" else "Consider carefully"
        }
        
        return {"analysis": analysis}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS & INSIGHTS ENDPOINTS
# ============================================================================

@app.get("/api/analytics/league")
async def get_league_analytics():
    """Get comprehensive league-wide analytics"""
    try:
        from src.database import execute_query

        # Get basic league stats
        teams = execute_query("SELECT * FROM fantasy_teams")
        players = execute_query("SELECT * FROM players WHERE is_active = 1")
        
        # Calculate league totals
        total_points_for = sum(team["points_for"] for team in teams)
        total_points_against = sum(team["points_against"] for team in teams)
        
        # Position distribution
        position_counts = {}
        for player in players:
            pos = player["position"]
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Team performance metrics
        team_metrics = []
        for team in teams:
            total_games = team["wins"] + team["losses"] + team["ties"]
            team_metrics.append({
                "team_name": team["team_name"],
                "points_for": team["points_for"],
                "points_against": team["points_against"],
                "win_pct": team["wins"] / max(1, total_games) if total_games > 0 else 0.0,
                "avg_points": team["points_for"] / max(1, total_games) if total_games > 0 else 0.0
            })
        
        # League averages
        league_avg_points = total_points_for / len(teams) if teams else 0
        
        analytics = {
            "league_summary": {
                "total_teams": len(teams),
                "total_active_players": len(players),
                "total_points_scored": total_points_for,
                "league_average_points": league_avg_points
            },
            "position_distribution": position_counts,
            "team_metrics": team_metrics,
            "highest_scoring_team": max(teams, key=lambda x: x["points_for"])["team_name"] if teams else None,
            "lowest_scoring_team": min(teams, key=lambda x: x["points_for"])["team_name"] if teams else None
        }
        
        return {"analytics": analytics}
    except Exception as e:
        logger.error(f"Error getting league analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/positional")
async def get_positional_analytics():
    """Get positional scarcity and distribution analysis"""
    try:
        from src.database import execute_query

        # Get players by position with team assignments
        players_query = """
        SELECT p.position, 
               COUNT(*) as total_players,
               COUNT(re.player_id) as rostered_players,
               COUNT(CASE WHEN re.is_starting = 1 THEN 1 END) as starting_players
        FROM players p
        LEFT JOIN roster_entries re ON p.id = re.player_id
        WHERE p.is_active = 1
        GROUP BY p.position
        ORDER BY p.position
        """
        position_stats = execute_query(players_query)
        
        # Calculate scarcity metrics
        positional_analysis = []
        for stats in position_stats:
            stats_dict = dict(stats)
            total = stats_dict["total_players"]
            rostered = stats_dict["rostered_players"]
            available = total - rostered
            
            scarcity_score = (rostered / total * 100) if total > 0 else 0
            
            positional_analysis.append({
                "position": stats_dict["position"],
                "total_players": total,
                "rostered_players": rostered,
                "available_players": available,
                "starting_players": stats_dict["starting_players"],
                "roster_percentage": scarcity_score,
                "scarcity_rating": "High" if scarcity_score > 80 else "Medium" if scarcity_score > 60 else "Low"
            })
        
        return {"positional_analysis": positional_analysis}
    except Exception as e:
        logger.error(f"Error getting positional analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/optimal-lineups")
async def get_optimal_lineups():
    """Get optimal lineup suggestions for all teams"""
    try:
        from src.database import execute_query

        teams = execute_query("SELECT id, team_name FROM fantasy_teams")
        
        optimal_lineups = []
        for team in teams:
            team_dict = dict(team)
            team_id = team_dict["id"]
            
            # Get team's players with recent projections
            roster_query = """
            SELECT p.*, re.is_starting,
                   pp.projected_fantasy_points
            FROM players p
            JOIN roster_entries re ON p.id = re.player_id
            LEFT JOIN player_projections pp ON p.id = pp.player_id
            WHERE re.fantasy_team_id = ?
            ORDER BY p.position, pp.projected_fantasy_points DESC NULLS LAST
            """
            players = execute_query(roster_query, (team_id,))
            
            # Simple optimal lineup logic (top projected player at each position)
            optimal_lineup = {}
            bench_players = []
            
            for player in players:
                player_dict = dict(player)
                position = player_dict["position"]
                
                if position not in optimal_lineup:
                    optimal_lineup[position] = player_dict
                else:
                    bench_players.append(player_dict)
            
            optimal_lineups.append({
                "team_id": team_id,
                "team_name": team_dict["team_name"],
                "optimal_lineup": optimal_lineup,
                "bench_players": bench_players[:10]  # Limit bench display
            })
        
        return {"optimal_lineups": optimal_lineups}
    except Exception as e:
        logger.error(f"Error getting optimal lineups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WAIVER WIRE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/waivers/recommendations")
async def get_waiver_recommendations():
    """Get waiver wire pickup recommendations"""
    try:
        from src.database import execute_query

        # Get available players with potential value
        available_query = """
        SELECT p.*, nt.team_name as nfl_team_name,
               pr.rank, pr.tier,
               pp.projected_fantasy_points
        FROM players p
        LEFT JOIN nfl_teams nt ON p.nfl_team_id = nt.id
        LEFT JOIN roster_entries re ON p.id = re.player_id
        LEFT JOIN player_rankings pr ON p.id = pr.player_id
        LEFT JOIN player_projections pp ON p.id = pp.player_id
        WHERE re.player_id IS NULL 
          AND p.is_active = 1
          AND (pr.rank IS NOT NULL OR pp.projected_fantasy_points IS NOT NULL)
        ORDER BY pr.rank ASC NULLS LAST, pp.projected_fantasy_points DESC NULLS LAST
        LIMIT 50
        """
        available_players = execute_query(available_query)
        
        # Group recommendations by position
        recommendations_by_position = {}
        for player in available_players:
            player_dict = dict(player)
            position = player_dict["position"]
            
            if position not in recommendations_by_position:
                recommendations_by_position[position] = []
            
            recommendations_by_position[position].append(player_dict)
        
        # Limit to top recommendations per position
        for position in recommendations_by_position:
            recommendations_by_position[position] = recommendations_by_position[position][:10]
        
        return {
            "recommendations": [dict(player) for player in available_players],
            "recommendations_by_position": recommendations_by_position,
            "total_recommendations": len(available_players)
        }
    except Exception as e:
        logger.error(f"Error getting waiver recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/waivers/priority")
async def get_waiver_priority():
    """Get current waiver priority order"""
    try:
        from src.database import execute_query

        priority_query = """
        SELECT wp.*, ft.team_name, ft.owner_name
        FROM waiver_priorities wp
        JOIN fantasy_teams ft ON wp.fantasy_team_id = ft.id
        ORDER BY wp.priority_order
        """
        priorities = execute_query(priority_query)
        
        return {
            "waiver_order": [dict(priority) for priority in priorities],
            "total_teams": len(priorities)
        }
    except Exception as e:
        logger.error(f"Error getting waiver priority: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
