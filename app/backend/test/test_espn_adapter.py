"""
Tests for ESPN adapter functionality
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest
from src.espn import convert_players, get_all_players, get_league_data
from src.logging_config import get_logger


@pytest.fixture
def mock_espn_league():
    """Create a mock ESPN league for testing"""
    mock_league = Mock()

    # Mock teams with rosters
    mock_team1 = Mock()

    # Create player 1
    player1 = Mock()
    player1.playerId = "1"
    player1.name = "Player 1"
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

    # Create player 2
    player2 = Mock()
    player2.playerId = "2"
    player2.name = "Player 2"
    player2.position = "RB"
    player2.proTeamId = "NE"
    player2.jersey = 12
    player2.height = "6-0"
    player2.weight = 220
    player2.age = 25
    player2.experience = 3
    player2.college = "Alabama"
    player2.injured = False
    player2.injuryStatus = "ACTIVE"
    player2.active = True

    mock_team1.roster = [player1, player2]

    mock_team2 = Mock()

    # Create player 3
    player3 = Mock()
    player3.playerId = "3"
    player3.name = "Player 3"
    player3.position = "WR"
    player3.proTeamId = "LV"
    player3.jersey = 17
    player3.height = "6-1"
    player3.weight = 215
    player3.age = 31
    player3.experience = 10
    player3.college = "Fresno State"
    player3.injured = False
    player3.injuryStatus = "ACTIVE"
    player3.active = True

    mock_team2.roster = [player3]

    mock_league.teams = [mock_team1, mock_team2]

    # Mock free agents as a method that returns a list
    # Create free agent 1
    free_agent1 = Mock()
    free_agent1.playerId = "4"
    free_agent1.name = "Free Agent 1"
    free_agent1.position = "TE"
    free_agent1.proTeamId = "BUF"
    free_agent1.jersey = 85
    free_agent1.height = "6-4"
    free_agent1.weight = 250
    free_agent1.age = 26
    free_agent1.experience = 4
    free_agent1.college = "Iowa"
    free_agent1.injured = False
    free_agent1.injuryStatus = "ACTIVE"
    free_agent1.active = True

    # Create free agent 2
    free_agent2 = Mock()
    free_agent2.playerId = "5"
    free_agent2.name = "Free Agent 2"
    free_agent2.position = "K"
    free_agent2.proTeamId = "SF"
    free_agent2.jersey = 9
    free_agent2.height = "6-1"
    free_agent2.weight = 190
    free_agent2.age = 29
    free_agent2.experience = 7
    free_agent2.college = "Georgia"
    free_agent2.injured = False
    free_agent2.injuryStatus = "ACTIVE"
    free_agent2.active = True

    mock_league.free_agents = Mock(return_value=[free_agent1, free_agent2])

    return mock_league


@pytest.fixture
def mock_espn_league_no_free_agents():
    """Create a mock ESPN league without free agents"""
    mock_league = Mock()

    mock_team1 = Mock()

    # Create player 1
    player1 = Mock()
    player1.playerId = "1"
    player1.name = "Player 1"
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

    mock_team1.roster = [player1]

    mock_league.teams = [mock_team1]

    # Mock free_agents to raise an exception
    mock_league.free_agents = Mock(side_effect=Exception("No free agents"))

    return mock_league


def test_get_all_players(mock_espn_league):
    """Test the get_all_players function"""
    all_players = get_all_players(mock_espn_league)

    # Should get 5 unique players (2 from team1 roster + 1 from team2 roster + 2 free agents)
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

    # Should get 5 players (2 from team1 roster + 1 from team2 roster + 2 free agents)
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
    mock_player = Mock()
    mock_player.playerId = "123"
    mock_player.name = "Injured Player"  # Set as string, not Mock
    mock_player.position = "RB"
    mock_player.proTeamId = "NE"
    mock_player.jersey = 12
    mock_player.height = "6-0"
    mock_player.weight = 220
    mock_player.age = 25
    mock_player.experience = 3
    mock_player.college = "Alabama"
    mock_player.injured = True
    mock_player.injuryStatus = "QUESTIONABLE"
    mock_player.active = True

    player = convert_player(mock_player)

    assert player.name == "Injured Player"
    assert player.position.value == "RB"
    assert player.nfl_team_id == "NE"
    assert player.is_injured == 1  # Should be converted to integer for SQLite
    assert player.injury_status == "QUESTIONABLE"


def test_convert_player_with_team_info():
    """Test converting a player with team information"""
    from espn import convert_player

    # Mock player with team info
    mock_player = Mock()
    mock_player.playerId = "456"
    mock_player.name = "Team Player"  # Set as string, not Mock
    mock_player.position = "QB"
    mock_player.proTeamId = "KC"
    mock_player.jersey = 15
    mock_player.height = "6-3"
    mock_player.weight = 225
    mock_player.age = 28
    mock_player.experience = 6
    mock_player.college = "Texas Tech"
    mock_player.injured = False
    mock_player.injuryStatus = "ACTIVE"
    mock_player.active = True

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
