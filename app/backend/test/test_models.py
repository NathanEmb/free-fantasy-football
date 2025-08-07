"""
Comprehensive test suite for data models

Tests cover:
- Model instantiation and validation
- Data type conversions
- Edge cases and error conditions
- Model relationships and constraints
- Serialization and deserialization
"""

import os
from dataclasses import asdict
from datetime import datetime

import pytest
from src.logging_config import get_logger
from src.models import (
    AcquisitionType,
    Conference,
    Division,
    FantasyMatchup,
    FantasyTeam,
    FantasyTeamWeeklyScore,
    FreeAgentRecommendation,
    GameStatus,
    LeagueConfig,
    NFLTeam,
    Platform,
    Player,
    PlayerGameStats,
    PlayerProjection,
    PlayerRanking,
    Position,
    RosterEntry,
    RosterPosition,
    ScoringType,
    TeamDefenseGameStats,
    TradeAnalysis,
    TradeItem,
    TradeProposal,
    TradeStatus,
    WaiverPriority,
)

logger = get_logger(__name__)


class TestPositionEnum:
    """Test Position enum functionality"""

    def test_position_values(self):
        """Test that all position values are correct"""
        assert Position.QB.value == "QB"
        assert Position.RB.value == "RB"
        assert Position.WR.value == "WR"
        assert Position.TE.value == "TE"
        assert Position.K.value == "K"
        assert Position.DEF.value == "DEF"
        assert Position.FLEX.value == "FLEX"
        assert Position.SUPERFLEX.value == "SUPERFLEX"

    def test_position_comparison(self):
        """Test position comparison"""
        assert Position.QB == Position.QB
        assert Position.QB != Position.RB
        assert str(Position.QB) == "Position.QB"


class TestPlatformEnum:
    """Test Platform enum functionality"""

    def test_platform_values(self):
        """Test that all platform values are correct"""
        assert Platform.ESPN.value == "ESPN"
        assert Platform.YAHOO.value == "Yahoo"
        assert Platform.SLEEPER.value == "Sleeper"
        assert Platform.CUSTOM.value == "Custom"


class TestScoringTypeEnum:
    """Test ScoringType enum functionality"""

    def test_scoring_type_values(self):
        """Test that all scoring type values are correct"""
        assert ScoringType.STANDARD.value == "Standard"
        assert ScoringType.PPR.value == "PPR"
        assert ScoringType.HALF_PPR.value == "Half-PPR"


class TestLeagueConfig:
    """Test LeagueConfig model"""

    def test_valid_league_config(self):
        """Test creating a valid LeagueConfig"""
        config = LeagueConfig(
            league_name="Test League",
            platform="ESPN",
            season_year=2024,
            platform_league_id="12345",
            scoring_type="PPR",
            team_count=12,
            playoff_teams=6,
        )

        assert config.league_name == "Test League"
        assert config.platform == "ESPN"
        assert config.season_year == 2024
        assert config.platform_league_id == "12345"
        assert config.scoring_type == "PPR"
        assert config.team_count == 12
        assert config.playoff_teams == 6
        assert config.is_active == 1

    def test_league_config_validation(self):
        """Test LeagueConfig validation"""
        # Test valid config
        config = LeagueConfig(
            league_name="Valid League",
            platform="ESPN",
            season_year=2024,
        )
        assert config.league_name == "Valid League"

        # Test invalid league name (too long)
        with pytest.raises(ValueError, match="League name must be 1-100 characters"):
            LeagueConfig(
                league_name="A" * 101,  # Too long
                platform="ESPN",
                season_year=2024,
            )

        # Test invalid season year
        with pytest.raises(ValueError, match="Season year must be 2000-2030"):
            LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=1999,  # Too early
            )

        with pytest.raises(ValueError, match="Season year must be 2000-2030"):
            LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2031,  # Too late
            )

        # Test invalid team count
        with pytest.raises(ValueError, match="Team count must be 2-32"):
            LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2024,
                team_count=1,  # Too few
            )

        with pytest.raises(ValueError, match="Team count must be 2-32"):
            LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2024,
                team_count=33,  # Too many
            )

        # Test invalid playoff teams
        with pytest.raises(ValueError, match="Playoff teams must be 2-16"):
            LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2024,
                playoff_teams=1,  # Too few
            )

        with pytest.raises(ValueError, match="Playoff teams must be 2-16"):
            LeagueConfig(
                league_name="Test League",
                platform="ESPN",
                season_year=2024,
                playoff_teams=17,  # Too many
            )


class TestFantasyTeam:
    """Test FantasyTeam model"""

    def test_valid_fantasy_team(self):
        """Test creating a valid FantasyTeam"""
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

        assert team.owner_name == "Test Owner"
        assert team.team_name == "Test Team"
        assert team.platform_team_id == "123"
        assert team.wins == 8
        assert team.losses == 5
        assert team.ties == 0
        assert team.points_for == 1200.5
        assert team.points_against == 1150.2

    def test_fantasy_team_validation(self):
        """Test FantasyTeam validation"""
        # Test valid team
        team = FantasyTeam(
            owner_name="Valid Owner",
            team_name="Valid Team",
        )
        assert team.owner_name == "Valid Owner"

        # Test invalid owner name (too long)
        with pytest.raises(ValueError, match="Owner name must be 1-100 characters"):
            FantasyTeam(
                owner_name="A" * 101,  # Too long
                team_name="Test Team",
            )

        # Test invalid team name (too long)
        with pytest.raises(ValueError, match="Team name must be 1-100 characters"):
            FantasyTeam(
                owner_name="Test Owner",
                team_name="A" * 101,  # Too long
            )

        # Test negative wins
        with pytest.raises(ValueError, match="Record values must be non-negative"):
            FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
                wins=-1,
            )

        # Test negative losses
        with pytest.raises(ValueError, match="Record values must be non-negative"):
            FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
                losses=-1,
            )

        # Test negative ties
        with pytest.raises(ValueError, match="Record values must be non-negative"):
            FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
                ties=-1,
            )

        # Test negative points
        with pytest.raises(ValueError, match="Points values must be non-negative"):
            FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
                points_for=-1.0,
            )

        with pytest.raises(ValueError, match="Points values must be non-negative"):
            FantasyTeam(
                owner_name="Test Owner",
                team_name="Test Team",
                points_against=-1.0,
            )


class TestPlayer:
    """Test Player model"""

    def test_valid_player(self):
        """Test creating a valid Player"""
        player = Player(
            name="Test Player",
            position=Position.QB,
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

        assert player.name == "Test Player"
        assert player.position.value == "QB"
        assert player.nfl_team_id == "KC"
        assert player.espn_id == "12345"
        assert player.jersey_number == 15
        assert player.height == "6-3"
        assert player.weight == 225
        assert player.age == 28
        assert player.experience_years == 6
        assert player.college == "Test College"
        assert player.is_injured == 0
        assert player.injury_status == "ACTIVE"
        assert player.is_active == 1

    def test_player_validation(self):
        """Test Player validation"""
        # Test valid player
        player = Player(
            name="Valid Player",
            position="QB",
        )
        assert player.name == "Valid Player"

        # Test invalid name (too long)
        with pytest.raises(ValueError, match="Player name must be 1-100 characters"):
            Player(
                name="A" * 101,  # Too long
                position="QB",
            )

        # Test invalid jersey number
        with pytest.raises(ValueError, match="Jersey number must be 0-99"):
            Player(
                name="Test Player",
                position="QB",
                jersey_number=100,  # Too high
            )

        with pytest.raises(ValueError, match="Jersey number must be 0-99"):
            Player(
                name="Test Player",
                position="QB",
                jersey_number=-1,  # Too low
            )

        # Test invalid weight
        with pytest.raises(ValueError, match="Weight must be 100-400 pounds"):
            Player(
                name="Test Player",
                position="QB",
                weight=50,  # Too low
            )

        with pytest.raises(ValueError, match="Weight must be 100-400 pounds"):
            Player(
                name="Test Player",
                position="QB",
                weight=500,  # Too high
            )

        # Test invalid age
        with pytest.raises(ValueError, match="Age must be 18-50"):
            Player(
                name="Test Player",
                position="QB",
                age=17,  # Too young
            )

        with pytest.raises(ValueError, match="Age must be 18-50"):
            Player(
                name="Test Player",
                position="QB",
                age=51,  # Too old
            )

        # Test invalid experience years
        with pytest.raises(ValueError, match="Experience years must be 0-25"):
            Player(
                name="Test Player",
                position="QB",
                experience_years=-1,  # Too low
            )

        with pytest.raises(ValueError, match="Experience years must be 0-25"):
            Player(
                name="Test Player",
                position="QB",
                experience_years=26,  # Too high
            )

    def test_player_with_optional_fields(self):
        """Test Player with optional fields set to None"""
        player = Player(
            name="Test Player",
            position=Position.QB,
            nfl_team_id=None,
            espn_id=None,
            jersey_number=None,
            height=None,
            weight=None,
            age=None,
            experience_years=None,
            college=None,
            injury_status=None,
        )

        assert player.name == "Test Player"
        assert player.position.value == "QB"
        assert player.nfl_team_id is None
        assert player.espn_id is None
        assert player.jersey_number is None
        assert player.height is None
        assert player.weight is None
        assert player.age is None
        assert player.experience_years is None
        assert player.college is None
        assert player.injury_status is None
        assert player.is_injured == 0  # Default
        assert player.is_active == 1  # Default


class TestRosterEntry:
    """Test RosterEntry model"""

    def test_valid_roster_entry(self):
        """Test creating a valid RosterEntry"""
        entry = RosterEntry(
            fantasy_team_id="team-123",
            player_id="player-456",
            roster_position_id="pos-789",
            is_starting=1,
            acquisition_type="Draft",
        )

        assert entry.fantasy_team_id == "team-123"
        assert entry.player_id == "player-456"
        assert entry.roster_position_id == "pos-789"
        assert entry.is_starting == 1
        assert entry.acquisition_type == "Draft"

    def test_roster_entry_defaults(self):
        """Test RosterEntry with default values"""
        entry = RosterEntry(
            fantasy_team_id="team-123",
            player_id="player-456",
        )

        assert entry.fantasy_team_id == "team-123"
        assert entry.player_id == "player-456"
        assert entry.roster_position_id is None
        assert entry.is_starting == 0  # Default
        assert entry.acquired_date is None
        assert entry.acquisition_type is None


class TestFantasyMatchup:
    """Test FantasyMatchup model"""

    def test_valid_fantasy_matchup(self):
        """Test creating a valid FantasyMatchup"""
        matchup = FantasyMatchup(
            week=1,
            home_team_id="team-123",
            away_team_id="team-456",
            home_score=120.5,
            away_score=115.2,
            winner_id="team-123",
            is_playoff=0,
        )

        assert matchup.week == 1
        assert matchup.home_team_id == "team-123"
        assert matchup.away_team_id == "team-456"
        assert matchup.home_score == 120.5
        assert matchup.away_score == 115.2
        assert matchup.winner_id == "team-123"
        assert matchup.is_playoff == 0

    def test_fantasy_matchup_validation(self):
        """Test FantasyMatchup validation"""
        # Test valid matchup
        matchup = FantasyMatchup(
            week=1,
            home_team_id="team-123",
            away_team_id="team-456",
        )
        assert matchup.week == 1

        # Test invalid week
        with pytest.raises(ValueError, match="Week must be 1-21"):
            FantasyMatchup(
                week=0,  # Too low
                home_team_id="team-123",
                away_team_id="team-456",
            )

        with pytest.raises(ValueError, match="Week must be 1-21"):
            FantasyMatchup(
                week=22,  # Too high
                home_team_id="team-123",
                away_team_id="team-456",
            )

        # Test negative scores
        with pytest.raises(ValueError, match="Scores must be non-negative"):
            FantasyMatchup(
                week=1,
                home_team_id="team-123",
                away_team_id="team-456",
                home_score=-1.0,
            )

        with pytest.raises(ValueError, match="Scores must be non-negative"):
            FantasyMatchup(
                week=1,
                home_team_id="team-123",
                away_team_id="team-456",
                away_score=-1.0,
            )


class TestNFLTeam:
    """Test NFLTeam model"""

    def test_valid_nfl_team(self):
        """Test creating a valid NFLTeam"""
        team = NFLTeam(
            team_code="KC",
            team_name="Kansas City Chiefs",
            city="Kansas City",
            conference=Conference.AFC,
            division=Division.WEST,
        )

        assert team.team_code == "KC"
        assert team.team_name == "Kansas City Chiefs"
        assert team.city == "Kansas City"
        assert team.conference.value == "AFC"
        assert team.division.value == "West"

    def test_nfl_team_validation(self):
        """Test NFLTeam validation"""
        # Test valid team
        team = NFLTeam(
            team_code="KC",
            team_name="Kansas City Chiefs",
            city="Kansas City",
            conference="AFC",
            division="West",
        )
        assert team.team_code == "KC"

        # Test invalid team code (too long)
        with pytest.raises(ValueError, match="Team code must be 1-3 characters"):
            NFLTeam(
                team_code="KCCH",  # Too long
                team_name="Kansas City Chiefs",
                city="Kansas City",
                conference="AFC",
                division="West",
            )

        # Test invalid team name (too long)
        with pytest.raises(ValueError, match="Team name must be 1-50 characters"):
            NFLTeam(
                team_code="KC",
                team_name="A" * 51,  # Too long
                city="Kansas City",
                conference="AFC",
                division="West",
            )

        # Test invalid city (too long)
        with pytest.raises(ValueError, match="City must be 1-30 characters"):
            NFLTeam(
                team_code="KC",
                team_name="Kansas City Chiefs",
                city="A" * 31,  # Too long
                conference="AFC",
                division="West",
            )


class TestRosterPosition:
    """Test RosterPosition model"""

    def test_valid_roster_position(self):
        """Test creating a valid RosterPosition"""
        position = RosterPosition(
            position=Position.QB,
            count=1,
            is_bench=0,
        )

        assert position.position.value == "QB"
        assert position.count == 1
        assert position.is_bench == 0

    def test_roster_position_validation(self):
        """Test RosterPosition validation"""
        # Test valid position
        position = RosterPosition(
            position=Position.QB,
            count=1,
        )
        assert position.position.value == "QB"

        # Test invalid count
        with pytest.raises(ValueError, match="Position count must be 0-10"):
            RosterPosition(
                position="QB",
                count=-1,  # Too low
            )

        with pytest.raises(ValueError, match="Position count must be 0-10"):
            RosterPosition(
                position="QB",
                count=11,  # Too high
            )


class TestPlayerGameStats:
    """Test PlayerGameStats model"""

    def test_valid_player_game_stats(self):
        """Test creating valid PlayerGameStats"""
        stats = PlayerGameStats(
            player_id="player-123",
            nfl_game_id="game-456",
            passing_yards=300,
            passing_touchdowns=3,
            rushing_yards=50,
            receiving_yards=100,
            fantasy_points=25.5,
        )

        assert stats.player_id == "player-123"
        assert stats.nfl_game_id == "game-456"
        assert stats.passing_yards == 300
        assert stats.passing_touchdowns == 3
        assert stats.rushing_yards == 50
        assert stats.receiving_yards == 100
        assert stats.fantasy_points == 25.5

    def test_player_game_stats_validation(self):
        """Test PlayerGameStats validation"""
        # Test valid stats
        stats = PlayerGameStats(
            player_id="player-123",
            nfl_game_id="game-456",
        )
        assert stats.player_id == "player-123"

        # Test negative stats
        with pytest.raises(ValueError, match="All stat values must be non-negative"):
            PlayerGameStats(
                player_id="player-123",
                nfl_game_id="game-456",
                passing_yards=-1,  # Negative
            )

        # Test negative fantasy points
        with pytest.raises(ValueError, match="Fantasy points must be non-negative"):
            PlayerGameStats(
                player_id="player-123",
                nfl_game_id="game-456",
                fantasy_points=-1.0,  # Negative
            )


class TestModelSerialization:
    """Test model serialization and deserialization"""

    def test_league_config_serialization(self):
        """Test LeagueConfig serialization"""
        config = LeagueConfig(
            league_name="Test League",
            platform="ESPN",
            season_year=2024,
        )

        # Convert to dict
        config_dict = asdict(config)

        assert config_dict["league_name"] == "Test League"
        assert config_dict["platform"] == "ESPN"
        assert config_dict["season_year"] == 2024
        assert "id" in config_dict
        assert "created_at" in config_dict
        assert "updated_at" in config_dict

    def test_player_serialization(self):
        """Test Player serialization"""
        player = Player(
            name="Test Player",
            position="QB",
            nfl_team_id="KC",
            espn_id="12345",
        )

        # Convert to dict
        player_dict = asdict(player)

        assert player_dict["name"] == "Test Player"
        assert player_dict["position"] == "QB"
        assert player_dict["nfl_team_id"] == "KC"
        assert player_dict["espn_id"] == "12345"
        assert "id" in player_dict
        assert "created_at" in player_dict
        assert "updated_at" in player_dict


class TestModelRelationships:
    """Test model relationships and constraints"""

    def test_roster_entry_relationships(self):
        """Test RosterEntry relationships"""
        # Create related objects
        team = FantasyTeam(
            owner_name="Test Owner",
            team_name="Test Team",
        )

        player = Player(
            name="Test Player",
            position="QB",
        )

        roster_position = RosterPosition(
            position="QB",
            count=1,
        )

        # Create roster entry linking them
        roster_entry = RosterEntry(
            fantasy_team_id=team.id,
            player_id=player.id,
            roster_position_id=roster_position.id,
            is_starting=1,
        )

        assert roster_entry.fantasy_team_id == team.id
        assert roster_entry.player_id == player.id
        assert roster_entry.roster_position_id == roster_position.id

    def test_matchup_relationships(self):
        """Test FantasyMatchup relationships"""
        # Create teams
        home_team = FantasyTeam(
            owner_name="Home Owner",
            team_name="Home Team",
        )

        away_team = FantasyTeam(
            owner_name="Away Owner",
            team_name="Away Team",
        )

        # Create matchup
        matchup = FantasyMatchup(
            week=1,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            winner_id=home_team.id,
        )

        assert matchup.home_team_id == home_team.id
        assert matchup.away_team_id == away_team.id
        assert matchup.winner_id == home_team.id


if __name__ == "__main__":
    pytest.main([__file__])
