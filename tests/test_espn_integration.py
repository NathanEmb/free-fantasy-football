"""
Comprehensive test suite for ESPN integration

Tests cover:
- ESPN API to core data model conversion
- Core data model to SQLite operations
- SQLite to core data model retrieval
- ESPN database initialization
- Error handling and edge cases
"""

import os
import shutil

# Add the app directory to the path so we can import modules
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "backend"))

from database import execute_query, get_db_connection, init_database
from espn import (
    ESPNFantasyError,
    convert_league_config,
    convert_matchup,
    convert_matchups,
    convert_player,
    convert_players,
    convert_roster_entries,
    convert_team,
    convert_teams,
    get_league_config_from_env,
    get_league_data,
    init_espn_data,
    validate_league_access,
)
from logging_config import get_logger
from models import FantasyMatchup, FantasyTeam, LeagueConfig, Player, RosterEntry

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


@pytest.fixture
def mock_espn_league():
    """Create a mock ESPN league for testing"""
    mock_league = Mock()

    # Mock league settings
    mock_league.settings.name = "Test Fantasy League"
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.settings.scoring_settings.reception = 1.0
    mock_league.settings.playoff_team_count = 6

    # Mock teams
    mock_team1 = Mock()
    mock_team1.team_id = 1
    mock_team1.team_name = "Team Alpha"
    mock_team1.wins = 8
    mock_team1.losses = 5
    mock_team1.ties = 0
    mock_team1.points_for = 1200.5
    mock_team1.points_against = 1150.2
    mock_team1.owners = [{"displayName": "John Doe"}]
    player1 = Mock()
    player1.playerId = "1"
    player1.name = "Patrick Mahomes"
    player1.position = "QB"
    player1.proTeamId = "KC"
    player1.jersey = 15
    player1.height = "6-3"
    player1.weight = 225
    player1.age = 28
    player1.experience = 6
    player1.college = "Texas Tech"
    player1.injured = False
    player1.injuryStatus = "ACTIVE"
    player1.active = True
    player1.starter = True

    player2 = Mock()
    player2.playerId = "2"
    player2.name = "Christian McCaffrey"
    player2.position = "RB"
    player2.proTeamId = "SF"
    player2.jersey = 23
    player2.height = "5-11"
    player2.weight = 205
    player2.age = 27
    player2.experience = 7
    player2.college = "Stanford"
    player2.injured = False
    player2.injuryStatus = "ACTIVE"
    player2.active = True
    player2.starter = True

    mock_team1.roster = [player1, player2]

    mock_team2 = Mock()
    mock_team2.team_id = 2
    mock_team2.team_name = "Team Beta"
    mock_team2.wins = 6
    mock_team2.losses = 7
    mock_team2.ties = 0
    mock_team2.points_for = 1100.3
    mock_team2.points_against = 1120.1
    mock_team2.owners = [{"displayName": "Jane Smith"}]
    player3 = Mock()
    player3.playerId = "3"
    player3.name = "Tyreek Hill"
    player3.position = "WR"
    player3.proTeamId = "MIA"
    player3.jersey = 10
    player3.height = "5-10"
    player3.weight = 185
    player3.age = 29
    player3.experience = 8
    player3.college = "West Alabama"
    player3.injured = False
    player3.injuryStatus = "ACTIVE"
    player3.active = True
    player3.starter = True

    mock_team2.roster = [player3]

    mock_league.teams = [mock_team1, mock_team2]

    # Mock free agents
    free_agent = Mock()
    free_agent.playerId = "4"
    free_agent.name = "Free Agent QB"
    free_agent.position = "QB"
    free_agent.proTeamId = "FA"
    free_agent.jersey = None
    free_agent.height = None
    free_agent.weight = None
    free_agent.age = None
    free_agent.experience = None
    free_agent.college = None
    free_agent.injured = False
    free_agent.injuryStatus = "ACTIVE"
    free_agent.active = True

    mock_league.free_agents = Mock(return_value=[free_agent])

    # Mock scoreboard/matchups
    mock_matchup = Mock()
    mock_matchup.home_team.team_id = 1
    mock_matchup.away_team.team_id = 2
    mock_matchup.home_score = 120.5
    mock_matchup.away_score = 115.2
    mock_matchup.winner = mock_team1
    mock_matchup.playoff = False

    mock_league.scoreboard = Mock(return_value=[mock_matchup])

    return mock_league


class TestESPNToCoreDataModel:
    """Test ESPN API to core data model conversion"""

    def test_convert_league_config(self, mock_espn_league):
        """Test converting ESPN league to LeagueConfig model"""
        league_config = convert_league_config(mock_espn_league)

        assert isinstance(league_config, LeagueConfig)
        assert league_config.league_name == "Test Fantasy League"
        assert league_config.platform_league_id == "12345"
        assert league_config.season_year == 2024
        assert league_config.team_count == 2
        assert league_config.playoff_teams == 6

    def test_convert_team(self, mock_espn_league):
        """Test converting ESPN team to FantasyTeam model"""
        espn_team = mock_espn_league.teams[0]
        team = convert_team(espn_team)

        assert isinstance(team, FantasyTeam)
        assert team.owner_name == "John Doe"
        assert team.team_name == "Team Alpha"
        assert team.platform_team_id == "1"
        assert team.wins == 8
        assert team.losses == 5
        assert team.ties == 0
        assert team.points_for == 1200.5
        assert team.points_against == 1150.2

    def test_convert_player(self, mock_espn_league):
        """Test converting ESPN player to Player model"""
        espn_player = mock_espn_league.teams[0].roster[0]
        player = convert_player(espn_player)

        assert isinstance(player, Player)
        assert player.name == "Patrick Mahomes"
        assert player.position.value == "QB"
        assert player.nfl_team_id == "KC"
        assert player.espn_id == "1"
        assert player.jersey_number == 15
        assert player.height == "6-3"
        assert player.weight == 225
        assert player.age == 28
        assert player.experience_years == 6
        assert player.college == "Texas Tech"
        assert player.is_injured == 0
        assert player.injury_status == "ACTIVE"
        assert player.is_active == 1

    def test_convert_player_with_injury(self, mock_espn_league):
        """Test converting injured player"""
        espn_player = Mock(
            playerId="5",
            name="Injured Player",
            position="RB",
            proTeamId="NE",
            injured=True,
            injuryStatus="QUESTIONABLE",
            active=True,
        )
        player = convert_player(espn_player)

        assert player.is_injured == 1
        assert player.injury_status == "QUESTIONABLE"

    def test_convert_player_defense_special_teams(self):
        """Test converting defense/special teams (handles list injury status)"""
        espn_player = Mock(
            playerId="6",
            name="Steelers D/ST",
            position="DEF",
            proTeamId="PIT",
            injured=False,
            injuryStatus=[],  # Empty list for D/ST
            active=True,
        )
        player = convert_player(espn_player)

        assert player.name == "Steelers D/ST"
        assert player.position.value == "DEF"
        assert player.injury_status is None

    def test_convert_teams(self, mock_espn_league):
        """Test converting all teams"""
        teams = convert_teams(mock_espn_league)

        assert len(teams) == 2
        assert all(isinstance(team, FantasyTeam) for team in teams)
        assert teams[0].team_name == "Team Alpha"
        assert teams[1].team_name == "Team Beta"

    def test_convert_players(self, mock_espn_league):
        """Test converting all players (including free agents)"""
        players = convert_players(mock_espn_league)

        # Should get 4 players: 3 from rosters + 1 free agent
        assert len(players) == 4

        player_names = [p.name for p in players]
        assert "Patrick Mahomes" in player_names
        assert "Christian McCaffrey" in player_names
        assert "Tyreek Hill" in player_names
        assert "Free Agent QB" in player_names

    def test_convert_roster_entries(self, mock_espn_league):
        """Test converting roster entries"""
        teams = convert_teams(mock_espn_league)
        players = convert_players(mock_espn_league)

        team_mapping = {team.platform_team_id: team.id for team in teams}
        player_mapping = {player.espn_id: player.id for player in players}

        roster_entries = convert_roster_entries(mock_espn_league, team_mapping, player_mapping)

        assert len(roster_entries) == 3  # 2 from team1 + 1 from team2
        assert all(isinstance(entry, RosterEntry) for entry in roster_entries)

    def test_convert_matchup(self, mock_espn_league):
        """Test converting single matchup"""
        teams = convert_teams(mock_espn_league)
        team_mapping = {team.platform_team_id: team.id for team in teams}

        espn_matchup = mock_espn_league.scoreboard()[0]
        matchup = convert_matchup(espn_matchup, team_mapping, week=1)

        assert isinstance(matchup, FantasyMatchup)
        assert matchup.week == 1
        assert matchup.home_score == 120.5
        assert matchup.away_score == 115.2
        assert matchup.is_playoff == 0

    def test_convert_matchups(self, mock_espn_league):
        """Test converting all matchups"""
        teams = convert_teams(mock_espn_league)
        team_mapping = {team.platform_team_id: team.id for team in teams}

        matchups = convert_matchups(mock_espn_league, team_mapping)

        assert len(matchups) == 1
        assert all(isinstance(matchup, FantasyMatchup) for matchup in matchups)


class TestCoreDataModelToSQLite:
    """Test core data model to SQLite operations"""

    def test_league_config_to_sqlite(self, temp_database):
        """Test storing LeagueConfig in SQLite"""
        with get_db_connection() as conn:
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

            # Verify insertion
            result = conn.execute("SELECT * FROM league_config WHERE id = ?", (league_config.id,))
            row = result.fetchone()
            assert row is not None
            assert row["league_name"] == "Test League"

    def test_fantasy_team_to_sqlite(self, temp_database):
        """Test storing FantasyTeam in SQLite"""
        with get_db_connection() as conn:
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

            # Verify insertion
            result = conn.execute("SELECT * FROM fantasy_teams WHERE id = ?", (team.id,))
            row = result.fetchone()
            assert row is not None
            assert row["team_name"] == "Test Team"
            assert row["owner_name"] == "Test Owner"

    def test_player_to_sqlite(self, temp_database):
        """Test storing Player in SQLite"""
        with get_db_connection() as conn:
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

            # Verify insertion
            result = conn.execute("SELECT * FROM players WHERE id = ?", (player.id,))
            row = result.fetchone()
            assert row is not None
            assert row["name"] == "Test Player"
            assert row["position"] == "QB"
            assert row["espn_id"] == "12345"


class TestSQLiteToCoreDataModel:
    """Test SQLite to core data model retrieval"""

    def test_league_config_from_sqlite(self, temp_database):
        """Test retrieving LeagueConfig from SQLite"""
        with get_db_connection() as conn:
            # Insert test data
            conn.execute(
                """
                INSERT INTO league_config (id, league_name, platform, platform_league_id, season_year, scoring_type, team_count, playoff_teams)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("test-id", "Test League", "ESPN", "12345", 2024, "PPR", 12, 6),
            )

            # Retrieve and verify
            result = conn.execute("SELECT * FROM league_config WHERE id = ?", ("test-id",))
            row = result.fetchone()

            assert row is not None
            assert row["league_name"] == "Test League"
            assert row["platform"] == "ESPN"
            assert row["season_year"] == 2024

    def test_fantasy_teams_from_sqlite(self, temp_database):
        """Test retrieving FantasyTeams from SQLite"""
        with get_db_connection() as conn:
            # Insert test data
            conn.execute(
                """
                INSERT INTO fantasy_teams (id, owner_name, team_name, platform_team_id, wins, losses, ties, points_for, points_against)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("team-1", "Owner 1", "Team Alpha", "123", 8, 5, 0, 1200.5, 1150.2),
            )
            conn.execute(
                """
                INSERT INTO fantasy_teams (id, owner_name, team_name, platform_team_id, wins, losses, ties, points_for, points_against)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("team-2", "Owner 2", "Team Beta", "456", 6, 7, 0, 1100.3, 1120.1),
            )

            # Retrieve and verify
            result = conn.execute("SELECT * FROM fantasy_teams ORDER BY team_name")
            rows = result.fetchall()

            assert len(rows) == 2
            assert rows[0]["team_name"] == "Team Alpha"
            assert rows[1]["team_name"] == "Team Beta"

    def test_players_from_sqlite(self, temp_database):
        """Test retrieving Players from SQLite"""
        with get_db_connection() as conn:
            # Insert test data
            conn.execute(
                """
                INSERT INTO players (id, name, position, espn_id, nfl_team_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("player-1", "Patrick Mahomes", "QB", "12345", "KC", 1),
            )
            conn.execute(
                """
                INSERT INTO players (id, name, position, espn_id, nfl_team_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("player-2", "Christian McCaffrey", "RB", "67890", "SF", 1),
            )

            # Retrieve and verify
            result = conn.execute("SELECT * FROM players ORDER BY name")
            rows = result.fetchall()

            assert len(rows) == 2
            assert rows[0]["name"] == "Christian McCaffrey"
            assert rows[1]["name"] == "Patrick Mahomes"


class TestESPNDatabaseInitialization:
    """Test ESPN database initialization"""

    @patch("espn_api.football.League")
    def test_init_espn_data_success(self, mock_espn_league_class, temp_database):
        """Test successful ESPN data initialization"""
        # Mock the ESPN league
        mock_league = Mock()
        mock_league.settings.name = "Test League"
        mock_league.league_id = 12345
        mock_league.year = 2024
        mock_league.settings.scoring_settings.reception = 1.0
        mock_league.settings.playoff_team_count = 6

        # Mock teams
        mock_team = Mock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.wins = 8
        mock_team.losses = 5
        mock_team.ties = 0
        mock_team.points_for = 1200.5
        mock_team.points_against = 1150.2
        mock_team.owners = [{"displayName": "Test Owner"}]
        mock_team.roster = []

        mock_league.teams = [mock_team]
        mock_league.free_agents = Mock(return_value=[])
        mock_league.scoreboard = Mock(return_value=[])

        mock_espn_league_class.return_value = mock_league

        # Test initialization
        success = init_espn_data()

        assert success is True

        # Verify data was inserted
        with get_db_connection() as conn:
            # Check league config
            result = conn.execute("SELECT COUNT(*) as count FROM league_config")
            assert result.fetchone()["count"] == 1

            # Check teams
            result = conn.execute("SELECT COUNT(*) as count FROM fantasy_teams")
            assert result.fetchone()["count"] == 1

    @patch("espn_api.football.League")
    def test_init_espn_data_validation_failure(self, mock_espn_league_class, temp_database):
        """Test ESPN data initialization with validation failure"""
        # Mock league access failure
        mock_espn_league_class.side_effect = Exception("League not found")

        success = init_espn_data()

        assert success is False

    def test_get_league_config_from_env(self):
        """Test getting league configuration from environment variables"""
        # Test with default values
        league_id, year = get_league_config_from_env()

        assert isinstance(league_id, int)
        assert isinstance(year, int)
        assert league_id == 24481082  # Default value
        assert year == 2024  # Default value


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_convert_player_missing_fields(self):
        """Test converting player with missing fields"""
        espn_player = Mock()
        espn_player.playerId = "123"
        espn_player.name = "Test Player"
        espn_player.position = "QB"
        espn_player.jersey = None
        espn_player.height = None
        espn_player.weight = None
        espn_player.age = None
        espn_player.experience = None
        espn_player.college = None
        espn_player.injured = False
        espn_player.injuryStatus = None
        espn_player.active = True
        # Missing most fields

        player = convert_player(espn_player)

        assert player.name == "Test Player"
        assert player.position.value == "QB"
        assert player.nfl_team_id is None
        assert player.espn_id == "123"
        assert player.is_injured == 0
        assert player.is_active == 1

    def test_convert_team_missing_owner(self):
        """Test converting team with missing owner information"""
        espn_team = Mock(
            team_id=1,
            team_name="Test Team",
            wins=8,
            losses=5,
            ties=0,
            points_for=1200.5,
            points_against=1150.2,
            owners=[],  # Empty owners list
        )

        team = convert_team(espn_team)

        assert team.owner_name == "Unknown Owner"
        assert team.team_name == "Test Team"

    def test_validate_league_access_success(self):
        """Test successful league access validation"""
        with patch("espn.ESPNLeague") as mock_espn_league_class:
            mock_league = Mock()
            mock_league.teams = [Mock(), Mock()]  # 2 teams
            mock_espn_league_class.return_value = mock_league

            result = validate_league_access(12345, 2024)
            assert result is True

    def test_validate_league_access_failure(self):
        """Test failed league access validation"""
        with patch("espn.ESPNLeague") as mock_espn_league_class:
            mock_espn_league_class.side_effect = Exception("League not found")

            result = validate_league_access(12345, 2024)
            assert result is False


class TestIntegration:
    """Integration tests combining multiple components"""

    @patch("espn_api.football.League")
    def test_full_espn_to_database_flow(self, mock_espn_league_class, temp_database):
        """Test complete flow from ESPN API to database"""
        # Setup mock ESPN league
        mock_league = Mock()
        mock_league.settings.name = "Integration Test League"
        mock_league.league_id = 12345
        mock_league.year = 2024
        mock_league.settings.scoring_settings.reception = 1.0
        mock_league.settings.playoff_team_count = 6

        mock_team = Mock()
        mock_team.team_id = 1
        mock_team.team_name = "Integration Team"
        mock_team.wins = 8
        mock_team.losses = 5
        mock_team.ties = 0
        mock_team.points_for = 1200.5
        mock_team.points_against = 1150.2
        mock_team.owners = [{"displayName": "Integration Owner"}]
        mock_team.roster = [
            Mock(
                playerId="1",
                name="Integration Player",
                position="QB",
                proTeamId="KC",
                injured=False,
                injuryStatus="ACTIVE",
                active=True,
            )
        ]

        mock_league.teams = [mock_team]
        mock_league.free_agents = Mock(return_value=[])
        mock_league.scoreboard = Mock(return_value=[])

        mock_espn_league_class.return_value = mock_league

        # Test the full flow
        success = init_espn_data()

        assert success is True

        # Verify data integrity
        with get_db_connection() as conn:
            # Check league config
            result = conn.execute("SELECT * FROM league_config")
            league_row = result.fetchone()
            assert league_row["league_name"] == "Integration Test League"

            # Check teams
            result = conn.execute("SELECT * FROM fantasy_teams")
            team_row = result.fetchone()
            assert team_row["team_name"] == "Integration Team"
            assert team_row["owner_name"] == "Integration Owner"

            # Check players
            result = conn.execute("SELECT * FROM players")
            player_row = result.fetchone()
            assert player_row["name"] == "Integration Player"
            assert player_row["position"] == "QB"


if __name__ == "__main__":
    pytest.main([__file__])
