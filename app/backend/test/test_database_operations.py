"""
Comprehensive test suite for database operations

Tests cover:
- Database initialization and schema
- CRUD operations for all models
- Data validation and constraints
- Error handling and edge cases
- Connection management
"""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime

import pytest
from src.database import (
    execute_delete,
    execute_insert,
    execute_query,
    execute_update,
    get_database_path,
    get_db_connection,
    init_database,
)
from src.logging_config import get_logger
from src.models import (
    Conference,
    Division,
    FantasyMatchup,
    FantasyTeam,
    LeagueConfig,
    NFLTeam,
    Platform,
    Player,
    Position,
    RosterEntry,
    RosterPosition,
    ScoringType,
)

logger = get_logger(__name__)


@pytest.fixture
def temp_database():
    """Create a temporary database for testing"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_fantasy_football.db")

    # Set environment variable for the test database
    original_db_path = os.getenv("SQLITE_DB_PATH")
    os.environ["SQLITE_DB_PATH"] = temp_db_path

    # Initialize the test database
    init_database()

    yield temp_db_path

    # Cleanup
    if original_db_path:
        os.environ["SQLITE_DB_PATH"] = original_db_path
    else:
        del os.environ["SQLITE_DB_PATH"]

    shutil.rmtree(temp_dir)


class TestDatabaseInitialization:
    """Test database initialization and schema"""

    def test_database_creation(self, temp_database):
        """Test that database is created with correct schema"""
        # The database should be created by the fixture
        assert os.path.exists(temp_database)

        with get_db_connection() as conn:
            # Check that all tables exist
            tables = [
                "league_config",
                "fantasy_teams",
                "players",
                "roster_entries",
                "fantasy_matchups",
                "nfl_teams",
                "roster_positions",
                "nfl_games",
                "player_game_stats",
                "team_defense_game_stats",
                "fantasy_team_weekly_scores",
                "player_projections",
                "player_rankings",
                "trade_proposals",
                "trade_items",
                "trade_analysis",  # Fixed: was trade_analyses
                "waiver_priorities",
                "free_agent_recommendations",
            ]

            for table in tables:
                result = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
                )
                assert result.fetchone() is not None, f"Table {table} not found"

    def test_database_path_configuration(self):
        """Test database path configuration"""
        path = get_database_path()
        assert isinstance(path, str)
        assert path.endswith(".db")

    def test_connection_context_manager(self, temp_database):
        """Test database connection context manager"""
        with get_db_connection() as conn:
            assert conn is not None
            # Test that we can execute a simple query
            result = conn.execute("SELECT 1 as test")
            row = result.fetchone()
            assert row["test"] == 1


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations"""

    def test_league_config_crud(self, temp_database):
        """Test CRUD operations for LeagueConfig"""
        with get_db_connection() as conn:
            # Create
            league_config = LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2024,
                platform_league_id="12345",
                scoring_type="PPR",
                team_count=12,
                playoff_teams=6,
            )

            conn.execute(
                """
                INSERT INTO league_config (id, league_name, platform, platform_league_id, season_year, scoring_type, team_count, playoff_teams)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    league_config.id,
                    league_config.league_name,
                    league_config.platform,
                    league_config.platform_league_id,
                    league_config.season_year,
                    league_config.scoring_type,
                    league_config.team_count,
                    league_config.playoff_teams,
                ),
            )

            # Read
            result = conn.execute("SELECT * FROM league_config WHERE id = ?", (league_config.id,))
            row = result.fetchone()
            assert row is not None
            assert row["league_name"] == "Test League"
            assert row["platform"] == "ESPN"

            # Update
            conn.execute(
                "UPDATE league_config SET league_name = ? WHERE id = ?",
                ("Updated Test League", league_config.id),
            )

            result = conn.execute(
                "SELECT league_name FROM league_config WHERE id = ?", (league_config.id,)
            )
            row = result.fetchone()
            assert row["league_name"] == "Updated Test League"

            # Delete
            conn.execute("DELETE FROM league_config WHERE id = ?", (league_config.id,))

            result = conn.execute(
                "SELECT COUNT(*) as count FROM league_config WHERE id = ?", (league_config.id,)
            )
            assert result.fetchone()["count"] == 0

    def test_fantasy_team_crud(self, temp_database):
        """Test CRUD operations for FantasyTeam"""
        with get_db_connection() as conn:
            # Create
            team = FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
                platform_team_id="123",
                wins=8,
                losses=5,
                ties=0,
                points_for=1200.5,
                points_against=1150.2,
            )

            conn.execute(
                """
                INSERT INTO fantasy_teams (id, owner_name, team_name, platform_team_id, wins, losses, ties, points_for, points_against)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    team.id,
                    team.owner_name,
                    team.team_name,
                    team.platform_team_id,
                    team.wins,
                    team.losses,
                    team.ties,
                    team.points_for,
                    team.points_against,
                ),
            )

            # Read
            result = conn.execute("SELECT * FROM fantasy_teams WHERE id = ?", (team.id,))
            row = result.fetchone()
            assert row is not None
            assert row["team_name"] == "Test Team"
            assert row["owner_name"] == "Test Owner"
            assert row["wins"] == 8
            assert row["losses"] == 5

            # Update
            conn.execute("UPDATE fantasy_teams SET wins = ? WHERE id = ?", (9, team.id))

            result = conn.execute("SELECT wins FROM fantasy_teams WHERE id = ?", (team.id,))
            row = result.fetchone()
            assert row["wins"] == 9

            # Delete
            conn.execute("DELETE FROM fantasy_teams WHERE id = ?", (team.id,))

            result = conn.execute(
                "SELECT COUNT(*) as count FROM fantasy_teams WHERE id = ?", (team.id,)
            )
            assert result.fetchone()["count"] == 0

    def test_player_crud(self, temp_database):
        """Test CRUD operations for Player"""
        with get_db_connection() as conn:
            # Create
            player = Player(
                name="Test Player",
                position="QB",
                nfl_team_id="KC",
                espn_id="12345",
                jersey_number=15,
                height="6-3",
                weight=225,
                age=28,
                experience_years=6,
                college="Test College",
                is_injured=0,
                injury_status="ACTIVE",
                is_active=1,
            )

            conn.execute(
                """
                INSERT INTO players (id, nfl_team_id, name, position, espn_id, jersey_number, height, weight, age, experience_years, college, is_injured, injury_status, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player.id,
                    player.nfl_team_id,
                    player.name,
                    player.position,
                    player.espn_id,
                    player.jersey_number,
                    player.height,
                    player.weight,
                    player.age,
                    player.experience_years,
                    player.college,
                    player.is_injured,
                    player.injury_status,
                    player.is_active,
                ),
            )

            # Read
            result = conn.execute("SELECT * FROM players WHERE id = ?", (player.id,))
            row = result.fetchone()
            assert row is not None
            assert row["name"] == "Test Player"
            assert row["position"] == "QB"
            assert row["espn_id"] == "12345"

            # Update
            conn.execute("UPDATE players SET jersey_number = ? WHERE id = ?", (16, player.id))

            result = conn.execute("SELECT jersey_number FROM players WHERE id = ?", (player.id,))
            row = result.fetchone()
            assert row["jersey_number"] == 16

            # Delete
            conn.execute("DELETE FROM players WHERE id = ?", (player.id,))

            result = conn.execute(
                "SELECT COUNT(*) as count FROM players WHERE id = ?", (player.id,)
            )
            assert result.fetchone()["count"] == 0


class TestDataValidation:
    """Test data validation and constraints"""

    def test_player_validation_constraints(self, temp_database):
        """Test player data validation constraints"""
        with get_db_connection() as conn:
            # Test valid player
            valid_player = Player(
                name="Valid Player",
                position="QB",
                jersey_number=15,
                weight=225,
                age=28,
                experience_years=6,
                is_injured=0,
                is_active=1,
            )

            # This should work
            conn.execute(
                """
                INSERT INTO players (id, name, position, jersey_number, weight, age, experience_years, is_injured, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    valid_player.id,
                    valid_player.name,
                    valid_player.position,
                    valid_player.jersey_number,
                    valid_player.weight,
                    valid_player.age,
                    valid_player.experience_years,
                    valid_player.is_injured,
                    valid_player.is_active,
                ),
            )

            # Test invalid jersey number (should be caught by model validation)
            with pytest.raises(ValueError):
                invalid_player = Player(
                    name="Invalid Player",
                    position="QB",
                    jersey_number=100,  # Invalid: > 99
                    is_injured=0,
                    is_active=1,
                )

            # Test invalid weight (should be caught by model validation)
            with pytest.raises(ValueError):
                invalid_player = Player(
                    name="Invalid Player",
                    position="QB",
                    weight=50,  # Invalid: < 100
                    is_injured=0,
                    is_active=1,
                )

    def test_fantasy_team_validation_constraints(self, temp_database):
        """Test fantasy team data validation constraints"""
        with get_db_connection() as conn:
            # Test valid team
            valid_team = FantasyTeam(
                owner_name="Valid Owner",
                team_name="Valid Team",
                wins=8,
                losses=5,
                ties=0,
                points_for=1200.5,
                points_against=1150.2,
            )

            # This should work
            conn.execute(
                """
                INSERT INTO fantasy_teams (id, owner_name, team_name, wins, losses, ties, points_for, points_against)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    valid_team.id,
                    valid_team.owner_name,
                    valid_team.team_name,
                    valid_team.wins,
                    valid_team.losses,
                    valid_team.ties,
                    valid_team.points_for,
                    valid_team.points_against,
                ),
            )

            # Test invalid record (should be caught by model validation)
            with pytest.raises(ValueError):
                invalid_team = FantasyTeam(
                    owner_name="Invalid Owner",
                    team_name="Invalid Team",
                    wins=-1,  # Invalid: negative
                    losses=5,
                    ties=0,
                    points_for=1200.5,
                    points_against=1150.2,
                )


class TestDatabaseUtilityFunctions:
    """Test database utility functions"""

    def test_execute_query(self, temp_database):
        """Test execute_query function"""
        # Clear any existing data first
        with get_db_connection() as conn:
            conn.execute("DELETE FROM fantasy_teams WHERE id = ?", ("test-id",))
            conn.commit()

            # Insert test data
            conn.execute(
                "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
                ("test-id", "Test Owner", "Test Team"),
            )
            conn.commit()

        # Test query execution
        results = execute_query("SELECT * FROM fantasy_teams WHERE id = ?", ("test-id",))

        assert len(results) == 1
        assert results[0]["owner_name"] == "Test Owner"
        assert results[0]["team_name"] == "Test Team"

    def test_execute_insert(self, temp_database):
        """Test execute_insert function"""
        row_id = execute_insert(
            "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
            ("insert-test-id", "Insert Owner", "Insert Team"),
        )

        assert row_id > 0

        # Verify insertion
        results = execute_query("SELECT * FROM fantasy_teams WHERE id = ?", ("insert-test-id",))
        assert len(results) == 1
        assert results[0]["owner_name"] == "Insert Owner"

    def test_execute_update(self, temp_database):
        """Test execute_update function"""
        # Insert test data
        execute_insert(
            "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
            ("update-test-id", "Original Owner", "Original Team"),
        )

        # Test update
        affected_rows = execute_update(
            "UPDATE fantasy_teams SET owner_name = ? WHERE id = ?",
            ("Updated Owner", "update-test-id"),
        )

        assert affected_rows == 1

        # Verify update
        results = execute_query(
            "SELECT owner_name FROM fantasy_teams WHERE id = ?", ("update-test-id",)
        )
        assert results[0]["owner_name"] == "Updated Owner"

    def test_execute_delete(self, temp_database):
        """Test execute_delete function"""
        # Insert test data
        execute_insert(
            "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
            ("delete-test-id", "Delete Owner", "Delete Team"),
        )

        # Test delete
        affected_rows = execute_delete(
            "DELETE FROM fantasy_teams WHERE id = ?", ("delete-test-id",)
        )

        assert affected_rows == 1

        # Verify deletion
        results = execute_query(
            "SELECT COUNT(*) as count FROM fantasy_teams WHERE id = ?", ("delete-test-id",)
        )
        assert results[0]["count"] == 0


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_sql_query(self, temp_database):
        """Test handling of invalid SQL queries"""
        with pytest.raises(Exception):
            execute_query("SELECT * FROM non_existent_table")

    def test_invalid_insert_data(self, temp_database):
        """Test handling of invalid insert data"""
        with pytest.raises(Exception):
            execute_insert(
                "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
                ("test-id", "Owner", "Team", "extra_column"),  # Too many values
            )

    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Temporarily set invalid database path
        original_path = os.getenv("SQLITE_DB_PATH")
        os.environ["SQLITE_DB_PATH"] = "/invalid/path/database.db"

        # Test that we get an error when trying to connect to invalid path
        with pytest.raises((OSError, sqlite3.OperationalError)):
            with get_db_connection() as conn:
                conn.execute("SELECT 1")

        # Restore original path
        if original_path:
            os.environ["SQLITE_DB_PATH"] = original_path
        else:
            del os.environ["SQLITE_DB_PATH"]


class TestDataIntegrity:
    """Test data integrity and relationships"""

    def test_foreign_key_constraints(self, temp_database):
        """Test foreign key constraints"""
        with get_db_connection() as conn:
            # Create a team first
            team = FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
            )

            conn.execute(
                """
                INSERT INTO fantasy_teams (id, owner_name, team_name)
                VALUES (?, ?, ?)
                """,
                (team.id, team.owner_name, team.team_name),
            )

            # Create a player
            player = Player(
                name="Test Player",
                position="QB",
            )

            conn.execute(
                """
                INSERT INTO players (id, name, position)
                VALUES (?, ?, ?)
                """,
                (player.id, player.name, player.position),
            )

            # Create a roster entry (should work)
            roster_entry = RosterEntry(
                fantasy_team_id=team.id,
                player_id=player.id,
            )

            conn.execute(
                """
                INSERT INTO roster_entries (id, fantasy_team_id, player_id)
                VALUES (?, ?, ?)
                """,
                (roster_entry.id, roster_entry.fantasy_team_id, roster_entry.player_id),
            )

            # Verify the relationship
            result = conn.execute(
                """
                SELECT ft.team_name, p.name 
                FROM roster_entries re
                JOIN fantasy_teams ft ON re.fantasy_team_id = ft.id
                JOIN players p ON re.player_id = p.id
                WHERE re.id = ?
                """,
                (roster_entry.id,),
            )

            row = result.fetchone()
            assert row is not None
            assert row["team_name"] == "Test Team"
            assert row["name"] == "Test Player"

    def test_data_consistency(self, temp_database):
        """Test data consistency across related tables"""
        with get_db_connection() as conn:
            # Clear existing data first
            conn.execute("DELETE FROM fantasy_teams")
            conn.execute("DELETE FROM league_config")
            conn.commit()

            # Insert test data
            league_config = LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2024,
                team_count=2,
            )

            conn.execute(
                """
                INSERT INTO league_config (id, league_name, platform, season_year, team_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    league_config.id,
                    league_config.league_name,
                    league_config.platform,
                    league_config.season_year,
                    league_config.team_count,
                ),
            )

            # Insert teams
            team1 = FantasyTeam(owner_name="Owner 1", team_name="Team 1")
            team2 = FantasyTeam(owner_name="Owner 2", team_name="Team 2")

            conn.execute(
                "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
                (team1.id, team1.owner_name, team1.team_name),
            )
            conn.execute(
                "INSERT INTO fantasy_teams (id, owner_name, team_name) VALUES (?, ?, ?)",
                (team2.id, team2.owner_name, team2.team_name),
            )
            conn.commit()

            # Verify team count matches league config
            result = conn.execute("SELECT COUNT(*) as count FROM fantasy_teams")
            team_count = result.fetchone()["count"]

            result = conn.execute(
                "SELECT team_count FROM league_config WHERE id = ?", (league_config.id,)
            )
            expected_count = result.fetchone()["team_count"]

            assert team_count == expected_count


if __name__ == "__main__":
    pytest.main([__file__])
