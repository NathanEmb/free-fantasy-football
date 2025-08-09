"""
Tests for the comprehensive fantasy football dashboard endpoints
"""

import pytest
import tempfile
import os
import uuid
from fastapi.testclient import TestClient


def _init_test_data():
    """Initialize minimal test data for dashboard endpoints"""
    from src.database import get_db_connection
    
    with get_db_connection() as conn:
        # Insert minimal NFL teams
        nfl_teams = [
            ("KC", "Kansas City Chiefs", "Kansas City", "AFC", "West"),
            ("BUF", "Buffalo Bills", "Buffalo", "AFC", "East"),
        ]
        
        for team_code, team_name, city, conference, division in nfl_teams:
            team_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO nfl_teams (id, team_code, team_name, city, conference, division) VALUES (?, ?, ?, ?, ?, ?)",
                (team_id, team_code, team_name, city, conference, division),
            )
        
        # Insert league config
        league_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO league_config (id, league_name, platform, season_year, scoring_type, team_count, playoff_teams) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (league_id, "Test League", "ESPN", 2024, "PPR", 2, 2),
        )
        
        # Insert fantasy teams
        team_ids = []
        for i, (owner_name, team_name) in enumerate([("Test Owner 1", "Test Team 1"), ("Test Owner 2", "Test Team 2")]):
            team_id = str(uuid.uuid4())
            team_ids.append(team_id)
            conn.execute(
                "INSERT INTO fantasy_teams (id, owner_name, team_name, platform_team_id, wins, losses, ties, points_for, points_against) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (team_id, owner_name, team_name, str(i + 1), 5, 5, 0, 1500.0, 1400.0),
            )
        
        # Insert roster positions
        position_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO roster_positions (id, position, count, is_bench) VALUES (?, ?, ?, ?)",
            (position_id, "QB", 1, 0),
        )
        
        # Insert a few test players
        player_ids = []
        nfl_team_cursor = conn.execute("SELECT id FROM nfl_teams LIMIT 1")
        nfl_team_id = nfl_team_cursor.fetchone()["id"]
        
        for name, position in [("Patrick Mahomes", "QB"), ("Josh Allen", "QB")]:
            player_id = str(uuid.uuid4())
            player_ids.append(player_id)
            conn.execute(
                "INSERT INTO players (id, nfl_team_id, name, position, is_active) VALUES (?, ?, ?, ?, ?)",
                (player_id, nfl_team_id, name, position, 1),
            )
        
        # Insert roster entries
        for i, (team_id, player_id) in enumerate(zip(team_ids, player_ids)):
            roster_entry_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO roster_entries (id, fantasy_team_id, player_id, roster_position_id, is_starting) VALUES (?, ?, ?, ?, ?)",
                (roster_entry_id, team_id, player_id, position_id, 1),
            )
        
        conn.commit()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with test database"""
    # Create a temporary database for testing
    test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
    os.close(test_db_fd)
    os.unlink(test_db_path)  # Remove the empty file so init_database will create schema
    
    # Set test database path
    original_db_path = os.environ.get('SQLITE_DB_PATH')
    os.environ['SQLITE_DB_PATH'] = test_db_path
    
    try:
        # Import app after setting environment variable
        from src.main import app
        from src.database import init_database, get_database_path, get_db_connection
        
        # Initialize test database with schema
        init_database()
        
        # Initialize with minimal test data
        _init_test_data()
        
        # Create test client without triggering startup event
        app.router.on_event = lambda x: lambda: None  # Disable startup event for tests
        
        with TestClient(app, base_url="http://testserver") as client:
            yield client
    finally:
        # Restore original database path
        if original_db_path:
            os.environ['SQLITE_DB_PATH'] = original_db_path
        elif 'SQLITE_DB_PATH' in os.environ:
            del os.environ['SQLITE_DB_PATH']
        
        # Clean up test database
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


class TestTeamEndpoints:
    """Test team management endpoints"""

    def test_get_league_standings(self, client):
        """Test league standings endpoint"""
        response = client.get("/api/teams/standings")
        assert response.status_code == 200
        data = response.json()
        assert "standings" in data
        assert len(data["standings"]) == 12  # Sample data has 12 teams
        
        # Check first team has expected fields
        first_team = data["standings"][0]
        assert "team_name" in first_team
        assert "wins" in first_team
        assert "losses" in first_team
        assert "points_for" in first_team
        assert "win_percentage" in first_team
        assert "rank" in first_team

    def test_get_team_details(self, client):
        """Test individual team details endpoint"""
        # First get a team ID from standings
        standings_response = client.get("/api/teams/standings")
        team_id = standings_response.json()["standings"][0]["id"]
        
        response = client.get(f"/api/teams/{team_id}")
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
        assert data["team"]["id"] == team_id
        assert "roster" in data["team"]
        assert "win_percentage" in data["team"]
        assert "point_differential" in data["team"]

    def test_get_team_details_not_found(self, client):
        """Test team details with invalid ID"""
        response = client.get("/api/teams/nonexistent-id")
        assert response.status_code == 404

    def test_get_team_roster(self, client):
        """Test team roster endpoint"""
        standings_response = client.get("/api/teams/standings")
        team_id = standings_response.json()["standings"][0]["id"]
        
        response = client.get(f"/api/teams/{team_id}/roster")
        assert response.status_code == 200
        data = response.json()
        assert "team_id" in data
        assert "starting_lineup" in data
        assert "bench" in data
        assert "total_players" in data
        assert "position_counts" in data

    def test_get_team_schedule(self, client):
        """Test team schedule endpoint"""
        standings_response = client.get("/api/teams/standings") 
        team_id = standings_response.json()["standings"][0]["id"]
        
        response = client.get(f"/api/teams/{team_id}/schedule")
        assert response.status_code == 200
        data = response.json()
        assert "team_id" in data
        assert "team_name" in data
        assert "schedule" in data

    def test_get_team_stats(self, client):
        """Test team statistics endpoint"""
        standings_response = client.get("/api/teams/standings")
        team_id = standings_response.json()["standings"][0]["id"]
        
        response = client.get(f"/api/teams/{team_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        stats = data["stats"]
        assert "team_id" in stats
        assert "record" in stats
        assert "scoring" in stats
        assert "weekly_scores" in stats


class TestPlayerEndpoints:
    """Test player analysis endpoints"""

    def test_get_available_players(self, client):
        """Test available players endpoint"""
        response = client.get("/api/players/available")
        assert response.status_code == 200
        data = response.json()
        assert "available_players" in data
        assert "available_by_position" in data
        assert "total_available" in data

    def test_get_player_rankings(self, client):
        """Test player rankings endpoint"""
        response = client.get("/api/players/rankings")
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert "rankings_by_position" in data
        assert "filters" in data

    def test_get_player_rankings_with_filter(self, client):
        """Test player rankings with position filter"""
        response = client.get("/api/players/rankings?position=QB")
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["position"] == "QB"

    def test_get_player_details(self, client):
        """Test individual player details"""
        # Get a player ID from the players endpoint
        players_response = client.get("/api/players")
        players = players_response.json()["players"]
        if players:
            player_id = players[0]["id"]
            
            response = client.get(f"/api/players/{player_id}")
            assert response.status_code == 200
            data = response.json()
            assert "player" in data
            assert data["player"]["id"] == player_id

    def test_get_player_projections(self, client):
        """Test player projections endpoint"""
        players_response = client.get("/api/players")
        players = players_response.json()["players"]
        if players:
            player_id = players[0]["id"]
            
            response = client.get(f"/api/players/{player_id}/projections")
            assert response.status_code == 200
            data = response.json()
            assert "player_id" in data
            assert "projections" in data

    def test_get_player_stats(self, client):
        """Test player statistics endpoint"""
        players_response = client.get("/api/players")
        players = players_response.json()["players"]
        if players:
            player_id = players[0]["id"]
            
            response = client.get(f"/api/players/{player_id}/stats")
            assert response.status_code == 200
            data = response.json()
            assert "player_id" in data
            assert "game_stats" in data
            assert "season_summary" in data

    def test_compare_players_missing_data(self, client):
        """Test player comparison with missing player data"""
        response = client.post("/api/players/compare", json=["id1"])
        assert response.status_code == 400

    def test_compare_players_empty_list(self, client):
        """Test player comparison with empty list"""
        response = client.post("/api/players/compare", json=[])
        assert response.status_code == 400


class TestMatchupEndpoints:
    """Test matchup analysis endpoints"""

    def test_get_all_matchups(self, client):
        """Test all matchups endpoint"""
        response = client.get("/api/matchups")
        assert response.status_code == 200
        data = response.json()
        assert "matchups" in data
        assert "matchups_by_week" in data
        assert "total_matchups" in data

    def test_get_matchups_by_week(self, client):
        """Test matchups by week endpoint"""
        response = client.get("/api/matchups/week/1")
        assert response.status_code == 200
        data = response.json()
        assert "week" in data
        assert "matchups" in data
        assert data["week"] == 1

    def test_get_matchup_details_not_found(self, client):
        """Test matchup details with invalid ID"""
        response = client.get("/api/matchups/nonexistent-id")
        assert response.status_code == 404


class TestAnalyticsEndpoints:
    """Test analytics and insights endpoints"""

    def test_get_league_analytics(self, client):
        """Test league analytics endpoint"""
        response = client.get("/api/analytics/league")
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        analytics = data["analytics"]
        assert "league_summary" in analytics
        assert "position_distribution" in analytics
        assert "team_metrics" in analytics
        
        # Check expected values from sample data
        summary = analytics["league_summary"]
        assert summary["total_teams"] == 12
        assert summary["total_active_players"] == 40

    def test_get_positional_analytics(self, client):
        """Test positional analytics endpoint"""
        response = client.get("/api/analytics/positional")
        assert response.status_code == 200
        data = response.json()
        assert "positional_analysis" in data
        
        # Check that all positions are represented
        positions = {p["position"] for p in data["positional_analysis"]}
        expected_positions = {"QB", "RB", "WR", "TE", "K", "DEF"}
        assert positions == expected_positions

    def test_get_optimal_lineups(self, client):
        """Test optimal lineups endpoint"""
        response = client.get("/api/analytics/optimal-lineups")
        assert response.status_code == 200
        data = response.json()
        assert "optimal_lineups" in data
        assert len(data["optimal_lineups"]) == 12  # One for each team


class TestTradeEndpoints:
    """Test trade analysis endpoints"""

    def test_get_trade_proposals(self, client):
        """Test trade proposals endpoint"""
        response = client.get("/api/trades/proposals")
        assert response.status_code == 200
        data = response.json()
        assert "proposals" in data
        assert "total_proposals" in data

    def test_analyze_trade(self, client):
        """Test trade analysis endpoint"""
        # Get some team IDs for testing
        standings_response = client.get("/api/teams/standings")
        teams = standings_response.json()["standings"]
        
        if len(teams) >= 2:
            team1_id = teams[0]["id"]
            team2_id = teams[1]["id"]
            
            response = client.post("/api/trades/analyze", params={
                "proposing_team_id": team1_id,
                "receiving_team_id": team2_id
            })
            assert response.status_code == 200
            data = response.json()
            assert "analysis" in data

    def test_create_trade_proposal_invalid_teams(self, client):
        """Test creating trade proposal with invalid teams"""
        response = client.post("/api/trades/proposals", params={
            "proposing_team_id": "invalid-id",
            "receiving_team_id": "invalid-id-2"
        })
        assert response.status_code == 400


class TestWaiverEndpoints:
    """Test waiver wire management endpoints"""

    def test_get_waiver_recommendations(self, client):
        """Test waiver recommendations endpoint"""
        response = client.get("/api/waivers/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "recommendations_by_position" in data
        assert "total_recommendations" in data

    def test_get_waiver_priority(self, client):
        """Test waiver priority endpoint"""
        response = client.get("/api/waivers/priority")
        assert response.status_code == 200
        data = response.json()
        assert "waiver_order" in data
        assert "total_teams" in data


class TestEndpointIntegration:
    """Integration tests for endpoint combinations"""

    def test_team_to_player_flow(self, client):
        """Test getting team details and then player details"""
        # Get team standings
        standings_response = client.get("/api/teams/standings")
        assert standings_response.status_code == 200
        
        teams = standings_response.json()["standings"]
        if teams:
            team_id = teams[0]["id"]
            
            # Get team roster
            roster_response = client.get(f"/api/teams/{team_id}/roster")
            assert roster_response.status_code == 200
            
            roster = roster_response.json()
            if roster["starting_lineup"]:
                player_id = roster["starting_lineup"][0]["id"]
                
                # Get player details
                player_response = client.get(f"/api/players/{player_id}")
                assert player_response.status_code == 200

    def test_analytics_consistency(self, client):
        """Test that analytics endpoints return consistent data"""
        # Get league analytics
        league_response = client.get("/api/analytics/league")
        assert league_response.status_code == 200
        
        # Get positional analytics  
        positional_response = client.get("/api/analytics/positional")
        assert positional_response.status_code == 200
        
        # Check consistency between endpoints
        league_data = league_response.json()["analytics"]
        positional_data = positional_response.json()["positional_analysis"]
        
        # Total players should be consistent
        league_total = league_data["league_summary"]["total_active_players"]
        positional_total = sum(p["total_players"] for p in positional_data)
        assert league_total == positional_total