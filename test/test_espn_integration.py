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
import tempfile
from unittest.mock import Mock, patch

import pytest
from src.database import execute_query, get_db_connection, init_database
from src.espn import (
    AcquisitionType,
    ESPNFantasyError,
    Platform,
    Position,
    ScoringType,
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
from src.logging_config import get_logger
from src.models import FantasyMatchup, FantasyTeam, LeagueConfig, Player, RosterEntry

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
    mock_team1.points_for = 120.5
    mock_team1.points_against = 115.2
    mock_team1.owners = [{"displayName": "John Doe"}]

    # Create proper mock players
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

    player2 = Mock()
    player2.playerId = "2"
    player2.name = "Davante Adams"
    player2.position = "WR"
    player2.proTeamId = "LV"
    player2.jersey = 17
    player2.height = "6-1"
    player2.weight = 215
    player2.age = 31
    player2.experience = 10
    player2.college = "Fresno State"
    player2.injured = False
    player2.injuryStatus = "ACTIVE"
    player2.active = True

    mock_team1.roster = [player1, player2]

    # Add a second team to meet minimum team count requirement
    mock_team2 = Mock()
    mock_team2.team_id = 2
    mock_team2.team_name = "Team Beta"
    mock_team2.wins = 6
    mock_team2.losses = 7
    mock_team2.ties = 0
    mock_team2.points_for = 110.3
    mock_team2.points_against = 112.1
    mock_team2.owners = [{"displayName": "Jane Smith"}]
    mock_team2.roster = []

    mock_league.teams = [mock_team1, mock_team2]
    mock_league.free_agents = Mock(return_value=[])
    mock_league.scoreboard = Mock(return_value=[])

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
        assert team.points_for == 120.5
        assert team.points_against == 115.2

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
        espn_player = Mock()
        espn_player.playerId = "5"
        espn_player.name = "Injured Player"  # Set as string, not Mock
        espn_player.position = "RB"
        espn_player.proTeamId = "NE"
        espn_player.jersey = 12
        espn_player.height = "6-0"
        espn_player.weight = 220
        espn_player.age = 25
        espn_player.experience = 3
        espn_player.college = "Alabama"
        espn_player.injured = True
        espn_player.injuryStatus = "QUESTIONABLE"
        espn_player.active = True

        player = convert_player(espn_player)

        assert player.name == "Injured Player"
        assert player.position.value == "RB"
        assert player.nfl_team_id == "NE"
        assert player.is_injured == 1
        assert player.injury_status == "QUESTIONABLE"

    def test_convert_player_defense_special_teams(self):
        """Test converting defense/special teams (handles list injury status)"""
        espn_player = Mock()
        espn_player.playerId = "6"
        espn_player.name = "Steelers D/ST"  # Set as string, not Mock
        espn_player.position = "DEF"
        espn_player.proTeamId = "PIT"
        espn_player.jersey = None
        espn_player.height = None
        espn_player.weight = None
        espn_player.age = None
        espn_player.experience = None
        espn_player.college = None
        espn_player.injured = False
        espn_player.injuryStatus = []  # Empty list for D/ST
        espn_player.active = True

        player = convert_player(espn_player)

        assert player.name == "Steelers D/ST"
        assert player.position.value == "DEF"
        assert player.nfl_team_id == "PIT"
        assert player.is_injured == 0
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

        # Should get 2 players: 1 from roster
        assert len(players) == 2

        player_names = [p.name for p in players]
        assert "Patrick Mahomes" in player_names
        assert "Davante Adams" in player_names

    def test_convert_roster_entries(self, mock_espn_league):
        """Test converting roster entries"""
        teams = convert_teams(mock_espn_league)
        players = convert_players(mock_espn_league)

        team_mapping = {team.platform_team_id: team.id for team in teams}
        player_mapping = {player.espn_id: player.id for player in players}

        roster_entries = convert_roster_entries(mock_espn_league, team_mapping, player_mapping)

        assert len(roster_entries) == 2  # 2 from team1
        assert all(isinstance(entry, RosterEntry) for entry in roster_entries)

    def test_convert_matchup(self, mock_espn_league):
        """Test converting a single matchup"""
        teams = convert_teams(mock_espn_league)
        team_mapping = {team.platform_team_id: team.id for team in teams}

        # Create a mock matchup
        mock_matchup = Mock()
        mock_matchup.home_team = mock_espn_league.teams[0]
        mock_matchup.away_team = mock_espn_league.teams[1]
        mock_matchup.home_score = 120.5
        mock_matchup.away_score = 115.2
        mock_matchup.winner = mock_espn_league.teams[0]
        mock_matchup.playoff = False

        # Mock the scoreboard to return our matchup
        mock_espn_league.scoreboard = Mock(return_value=[mock_matchup])

        matchup = convert_matchup(mock_matchup, team_mapping, week=1)

        assert matchup is not None
        assert matchup.week == 1
        assert matchup.home_team_id == team_mapping["1"]
        assert matchup.away_team_id == team_mapping["2"]
        assert matchup.home_score == 120.5
        assert matchup.away_score == 115.2
        assert matchup.winner_id == team_mapping["1"]
        assert matchup.is_playoff == False

    def test_convert_matchups(self, mock_espn_league):
        """Test converting all matchups"""
        teams = convert_teams(mock_espn_league)
        team_mapping = {team.platform_team_id: team.id for team in teams}

        matchups = convert_matchups(mock_espn_league, team_mapping)

        assert len(matchups) == 0  # No matchups in mock league


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
            # Clean up any existing data first
            conn.execute("DELETE FROM fantasy_teams")

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
                ("player-2", "Davante Adams", "WR", "67890", "LV", 1),
            )

            # Retrieve and verify
            result = conn.execute("SELECT * FROM players ORDER BY name")
            rows = result.fetchall()

            assert len(rows) == 2
            assert rows[0]["name"] == "Davante Adams"
            assert rows[1]["name"] == "Patrick Mahomes"


class TestESPNDatabaseInitialization:
    """Test ESPN database initialization"""

    @patch("src.espn.get_league_data")
    def test_init_espn_data_success(self, mock_get_league_data, temp_database):
        """Test successful ESPN data initialization"""
        # Mock the get_league_data function to return test data
        mock_league_config = Mock()
        mock_league_config.league_name = "Test League"
        mock_league_config.platform = Platform.ESPN
        mock_league_config.platform_league_id = "12345"
        mock_league_config.season_year = 2024
        mock_league_config.scoring_type = ScoringType.PPR
        mock_league_config.team_count = 2
        mock_league_config.playoff_teams = 6

        mock_team = Mock()
        mock_team.id = "team-1"
        mock_team.owner_name = "Test Owner"
        mock_team.team_name = "Test Team"
        mock_team.platform_team_id = "1"
        mock_team.wins = 8
        mock_team.losses = 5
        mock_team.ties = 0
        mock_team.points_for = 1200.5
        mock_team.points_against = 1150.2

        mock_player = Mock()
        mock_player.id = "player-1"
        mock_player.name = "Test Player"
        mock_player.position = Position.QB
        mock_player.espn_id = "123"
        mock_player.nfl_team_id = "KC"
        mock_player.jersey_number = 15
        mock_player.height = "6-3"
        mock_player.weight = 225
        mock_player.age = 28
        mock_player.experience_years = 6
        mock_player.college = "Texas Tech"
        mock_player.is_injured = 0
        mock_player.injury_status = "ACTIVE"
        mock_player.is_active = 1

        mock_roster_entry = Mock()
        mock_roster_entry.id = "roster-1"
        mock_roster_entry.fantasy_team_id = "team-1"
        mock_roster_entry.player_id = "player-1"
        mock_roster_entry.is_starting = 1
        mock_roster_entry.acquisition_type = AcquisitionType.DRAFT

        mock_matchup = Mock()
        mock_matchup.id = "matchup-1"
        mock_matchup.week = 1
        mock_matchup.home_team_id = "team-1"
        mock_matchup.away_team_id = "team-2"
        mock_matchup.home_score = 120.5
        mock_matchup.away_score = 115.2
        mock_matchup.winner_id = "team-1"
        mock_matchup.is_playoff = 0

        mock_get_league_data.return_value = (
            mock_league_config,
            [mock_team],
            [mock_player],
            [mock_roster_entry],
            [mock_matchup],
        )

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

    @patch("src.espn.get_league_data")
    def test_init_espn_data_validation_failure(self, mock_get_league_data, temp_database):
        """Test ESPN data initialization with validation failure"""
        # Mock get_league_data to raise an exception
        mock_get_league_data.side_effect = Exception("League not found")

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
        espn_player.proTeamId = None  # Set to None explicitly
        espn_player.jersey = None
        espn_player.height = None
        espn_player.weight = None
        espn_player.age = None
        espn_player.experience = None
        espn_player.college = None
        espn_player.injured = False
        espn_player.injuryStatus = None
        espn_player.active = True

        player = convert_player(espn_player)

        assert player.name == "Test Player"
        assert player.position.value == "QB"
        assert player.nfl_team_id is None
        assert player.jersey_number is None
        assert player.height is None
        assert player.weight is None
        assert player.age is None
        assert player.experience_years is None
        assert player.college is None
        assert player.is_injured == 0
        assert player.injury_status is None
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
        with patch("src.espn.ESPNLeague") as mock_espn_league_class:
            mock_league = Mock()
            mock_league.teams = [Mock(), Mock()]  # 2 teams
            mock_espn_league_class.return_value = mock_league

            result = validate_league_access(12345, 2024)
            assert result is True

    def test_validate_league_access_failure(self):
        """Test failed league access validation"""
        with patch("src.espn.ESPNLeague") as mock_espn_league_class:
            mock_espn_league_class.side_effect = Exception("League not found")

            result = validate_league_access(12345, 2024)
            assert result is False


class TestIntegration:
    """Integration tests combining multiple components"""

    @patch("src.espn.get_league_data")
    def test_full_espn_to_database_flow(self, mock_get_league_data, temp_database):
        """Test complete flow from ESPN API to database"""
        # Setup mock data
        mock_league_config = Mock()
        mock_league_config.league_name = "Integration Test League"
        mock_league_config.platform = Platform.ESPN
        mock_league_config.platform_league_id = "12345"
        mock_league_config.season_year = 2024
        mock_league_config.scoring_type = ScoringType.PPR
        mock_league_config.team_count = 2
        mock_league_config.playoff_teams = 6

        mock_team = Mock()
        mock_team.id = "team-1"
        mock_team.owner_name = "Integration Owner"
        mock_team.team_name = "Integration Team"
        mock_team.platform_team_id = "1"
        mock_team.wins = 8
        mock_team.losses = 5
        mock_team.ties = 0
        mock_team.points_for = 1200.5
        mock_team.points_against = 1150.2

        mock_player = Mock()
        mock_player.id = "player-1"
        mock_player.name = "Integration Player"
        mock_player.position = Position.QB
        mock_player.espn_id = "123"
        mock_player.nfl_team_id = "KC"
        mock_player.jersey_number = 15
        mock_player.height = "6-3"
        mock_player.weight = 225
        mock_player.age = 28
        mock_player.experience_years = 6
        mock_player.college = "Texas Tech"
        mock_player.is_injured = 0
        mock_player.injury_status = "ACTIVE"
        mock_player.is_active = 1

        mock_roster_entry = Mock()
        mock_roster_entry.id = "roster-1"
        mock_roster_entry.fantasy_team_id = "team-1"
        mock_roster_entry.player_id = "player-1"
        mock_roster_entry.is_starting = 1
        mock_roster_entry.acquisition_type = AcquisitionType.DRAFT

        mock_matchup = Mock()
        mock_matchup.id = "matchup-1"
        mock_matchup.week = 1
        mock_matchup.home_team_id = "team-1"
        mock_matchup.away_team_id = "team-2"
        mock_matchup.home_score = 120.5
        mock_matchup.away_score = 115.2
        mock_matchup.winner_id = "team-1"
        mock_matchup.is_playoff = 0

        mock_get_league_data.return_value = (
            mock_league_config,
            [mock_team],
            [mock_player],
            [mock_roster_entry],
            [mock_matchup],
        )

        # Test the full flow
        success = init_espn_data()

        assert success is True

        # Verify data integrity
        with get_db_connection() as conn:
            # Check league config
            result = conn.execute("SELECT * FROM league_config")
            league_row = result.fetchone()
            assert league_row["league_name"] == "Integration Test League"


if __name__ == "__main__":
    pytest.main([__file__])
