"""
Tests for ESPN adapter functionality
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "backend"))

from espn import convert_players, get_all_players, get_league_data
from logging_config import get_logger


@pytest.fixture
def mock_espn_league():
    """Create a mock ESPN league for testing"""
    mock_league = Mock()

    # Mock teams with rosters
    mock_team1 = Mock()
    mock_team1.roster = [
        Mock(playerId="1", name="Player 1", position="QB"),
        Mock(playerId="2", name="Player 2", position="RB"),
    ]

    mock_team2 = Mock()
    mock_team2.roster = [
        Mock(playerId="3", name="Player 3", position="WR"),
        Mock(playerId="1", name="Player 1", position="QB"),  # Duplicate
    ]

    mock_league.teams = [mock_team1, mock_team2]

    # Mock free agents
    mock_league.free_agents = [
        Mock(playerId="4", name="Free Agent 1", position="TE"),
        Mock(playerId="5", name="Free Agent 2", position="K"),
    ]

    return mock_league


@pytest.fixture
def mock_espn_league_no_free_agents():
    """Create a mock ESPN league without free agents"""
    mock_league = Mock()

    mock_team1 = Mock()
    mock_team1.roster = [
        Mock(playerId="1", name="Player 1", position="QB"),
    ]

    mock_league.teams = [mock_team1]

    # Remove free_agents attribute
    if hasattr(mock_league, "free_agents"):
        delattr(mock_league, "free_agents")

    return mock_league


def test_get_all_players(mock_espn_league):
    """Test the get_all_players function"""
    all_players = get_all_players(mock_espn_league)

    # Should get 5 unique players (3 from rosters + 2 free agents)
    assert len(all_players) == 5

    # Check that we have the expected players
    player_ids = [str(getattr(p, "playerId", "")) for p in all_players]
    assert "1" in player_ids  # From roster
    assert "2" in player_ids  # From roster
    assert "3" in player_ids  # From roster
    assert "4" in player_ids  # From free agents
    assert "5" in player_ids  # From free agents


def test_get_all_players_no_free_agents(mock_espn_league_no_free_agents):
    """Test get_all_players when free_agents attribute doesn't exist"""
    all_players = get_all_players(mock_espn_league_no_free_agents)

    # Should get 1 player from roster
    assert len(all_players) == 1

    # Check that we have the expected player
    player_ids = [str(getattr(p, "playerId", "")) for p in all_players]
    assert "1" in player_ids


def test_convert_players(mock_espn_league):
    """Test the convert_players function"""
    players = convert_players(mock_espn_league)

    # Should get 5 players (3 from rosters + 2 free agents)
    assert len(players) == 5

    # Check that we have the expected players
    player_names = [p.name for p in players]
    assert "Player 1" in player_names
    assert "Player 2" in player_names
    assert "Player 3" in player_names
    assert "Free Agent 1" in player_names
    assert "Free Agent 2" in player_names


@pytest.mark.integration
def test_real_espn_league():
    """Test with real ESPN league data (integration test)"""
    logger = get_logger(__name__)
    league_id = int(os.getenv("ESPN_LEAGUE_ID", "24481082"))
    year = int(os.getenv("ESPN_YEAR", "2024"))

    try:
        # Test get_league_data
        league_config, teams, players, roster_entries, matchups = get_league_data(league_id, year)

        # Basic assertions
        assert league_config is not None
        assert len(teams) > 0
        assert len(players) > 0
        assert len(roster_entries) > 0
        assert len(matchups) > 0

        # Check if we got more players than before (should include free agents)
        if len(players) > 173:  # Previous count was 173
            logger.info(f"✅ Successfully got {len(players)} players (including free agents)")
        else:
            logger.warning(
                f"⚠️  Got {len(players)} players (same as before - may not have free agents)"
            )

        # Show some player examples
        logger.info(f"\n📋 Sample Players:")
        for i, player in enumerate(players[:5]):
            logger.info(
                f"  {i + 1}. {player.name} ({player.position.value}) - ESPN ID: {player.espn_id}"
            )

    except Exception as e:
        pytest.fail(f"Real ESPN test failed: {e}")

    def test_convert_player_with_injury_status():
        """Test converting a player with injury status"""
        from espn import convert_player

    # Mock injured player
    mock_player = Mock(
        playerId="123",
        name="Injured Player",
        position="RB",
        injured=True,
        injuryStatus="QUESTIONABLE",
    )

    player = convert_player(mock_player)

    assert player.name == "Injured Player"
    assert player.position.value == "RB"
    assert player.is_injured == 1  # Should be converted to integer for SQLite
    assert player.injury_status == "QUESTIONABLE"

    def test_convert_player_with_team_info():
        """Test converting a player with team information"""
        from espn import convert_player

    # Mock player with team info
    mock_player = Mock(
        playerId="456",
        name="Team Player",
        position="QB",
        proTeamId="KC",
        jersey=15,
        height="6-3",
        weight=225,
        age=28,
        experience=6,
        college="Texas Tech",
        injured=False,
        injuryStatus="ACTIVE",
    )

    player = convert_player(mock_player)

    assert player.name == "Team Player"
    assert player.position.value == "QB"
    assert player.nfl_team_id == "KC"
    assert player.jersey_number == 15
    assert player.height == "6-3"
    assert player.weight == 225
    assert player.age == 28
    assert player.experience_years == 6
    assert player.college == "Texas Tech"
    assert player.is_injured == 0
    assert player.injury_status == "ACTIVE"
