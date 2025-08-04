"""
ESPN API Adapter

This module provides adapter functions to convert data from the espn_api library
into our core data models for database storage and analysis.
"""

import logging
from typing import Any

from espn_api.football import League as ESPNLeague
from espn_api.football import Player as ESPNPlayer
from espn_api.football import Team as ESPNTeam
from models import (
    AcquisitionType,
    FantasyMatchup,
    FantasyTeam,
    LeagueConfig,
    Platform,
    Player,
    Position,
    RosterEntry,
    ScoringType,
)

# Configure logging
logger = logging.getLogger(__name__)


class ESPNAdapterError(Exception):
    """Custom exception for ESPN adapter errors"""

    pass


def determine_scoring_type(espn_league: ESPNLeague) -> ScoringType:
    """Determine scoring type from ESPN league settings"""
    try:
        # Check if PPR scoring is enabled
        if hasattr(espn_league.settings, "scoring_settings"):
            scoring = espn_league.settings.scoring_settings
            if hasattr(scoring, "reception") and scoring.reception == 1.0:
                return ScoringType.PPR
            elif hasattr(scoring, "reception") and scoring.reception == 0.5:
                return ScoringType.HALF_PPR

        # Default to standard if we can't determine
        return ScoringType.STANDARD
    except Exception as e:
        logger.warning(f"Could not determine scoring type: {e}")
        return ScoringType.STANDARD


def map_espn_position(espn_position: str) -> Position:
    """Map ESPN position to our Position enum"""
    position_mapping = {
        "QB": Position.QB,
        "RB": Position.RB,
        "WR": Position.WR,
        "TE": Position.TE,
        "K": Position.K,
        "DEF": Position.DEF,
        "FLEX": Position.FLEX,
        "SUPERFLEX": Position.SUPERFLEX,
    }
    return position_mapping.get(espn_position, Position.QB)


def convert_league_config(espn_league: ESPNLeague) -> LeagueConfig:
    """Convert ESPN League to LeagueConfig model"""
    try:
        return LeagueConfig(
            league_name=espn_league.settings.name,
            platform=Platform.ESPN,
            platform_league_id=str(espn_league.league_id),
            season_year=espn_league.year,
            scoring_type=determine_scoring_type(espn_league),
            team_count=len(espn_league.teams),
            playoff_teams=getattr(espn_league.settings, "playoff_team_count", 0),
        )
    except Exception as e:
        raise ESPNAdapterError(f"Failed to convert league config: {e}")


def convert_team(espn_team: ESPNTeam) -> FantasyTeam:
    """Convert ESPN Team to FantasyTeam model"""
    try:
        # Extract owner name from the owner dict
        owner_name = "Unknown Owner"
        if hasattr(espn_team, "owners") and espn_team.owners:
            owner = espn_team.owners[0]
            if isinstance(owner, dict) and "displayName" in owner:
                owner_name = owner["displayName"]
            elif isinstance(owner, str):
                owner_name = owner
            else:
                # Fallback: try to get any string representation
                owner_name = str(owner)

        return FantasyTeam(
            owner_name=owner_name,
            team_name=espn_team.team_name,
            platform_team_id=str(espn_team.team_id),
            wins=espn_team.wins,
            losses=espn_team.losses,
            ties=espn_team.ties,
            points_for=espn_team.points_for,
            points_against=espn_team.points_against,
        )
    except Exception as e:
        raise ESPNAdapterError(f"Failed to convert team {espn_team.team_name}: {e}")


def convert_teams(espn_league: ESPNLeague) -> list[FantasyTeam]:
    """Convert all ESPN teams to FantasyTeam models"""
    teams = []
    for espn_team in espn_league.teams:
        try:
            teams.append(convert_team(espn_team))
        except Exception as e:
            logger.warning(f"Failed to convert team: {e}")
            continue
    return teams


def convert_player(espn_player: ESPNPlayer) -> Player:
    """Convert ESPN Player to Player model"""
    try:
        # Extract player details
        player_name = getattr(espn_player, "name", "Unknown Player")
        position = map_espn_position(getattr(espn_player, "position", "QB"))
        espn_id = str(getattr(espn_player, "playerId", ""))

        # Get additional player details if available
        nfl_team_id = None
        if hasattr(espn_player, "proTeamId") and espn_player.proTeamId:
            nfl_team_id = str(espn_player.proTeamId)

        jersey_number = getattr(espn_player, "jersey", None)
        height = getattr(espn_player, "height", None)
        weight = getattr(espn_player, "weight", None)
        age = getattr(espn_player, "age", None)
        experience_years = getattr(espn_player, "experience", None)
        college = getattr(espn_player, "college", None)
        is_injured = getattr(espn_player, "injured", False)
        injury_status = getattr(espn_player, "injuryStatus", None)

        return Player(
            espn_id=espn_id,
            name=player_name,
            position=position,
            nfl_team_id=nfl_team_id,
            jersey_number=jersey_number,
            height=height,
            weight=weight,
            age=age,
            experience_years=experience_years,
            college=college,
            is_injured=is_injured,
            injury_status=injury_status,
        )
    except Exception as e:
        raise ESPNAdapterError(
            f"Failed to convert player {getattr(espn_player, 'name', 'Unknown')}: {e}"
        )


def get_all_players(espn_league: ESPNLeague) -> list[ESPNPlayer]:
    """Get all available players including free agents"""
    all_players = []
    seen_players = set()

    # Get players from team rosters
    for espn_team in espn_league.teams:
        for espn_player in espn_team.roster:
            espn_id = str(getattr(espn_player, "playerId", ""))
            if espn_id and espn_id not in seen_players:
                all_players.append(espn_player)
                seen_players.add(espn_id)

    # Get free agents (available players)
    try:
        # ESPN API provides free agents through the league object
        if hasattr(espn_league, "free_agents"):
            for espn_player in espn_league.free_agents:
                espn_id = str(getattr(espn_player, "playerId", ""))
                if espn_id and espn_id not in seen_players:
                    all_players.append(espn_player)
                    seen_players.add(espn_id)
    except Exception as e:
        logger.warning(f"Could not fetch free agents: {e}")

    # Try alternative method to get all players
    try:
        # Some ESPN API versions provide all players through a different method
        if hasattr(espn_league, "all_players"):
            for espn_player in espn_league.all_players:
                espn_id = str(getattr(espn_player, "playerId", ""))
                if espn_id and espn_id not in seen_players:
                    all_players.append(espn_player)
                    seen_players.add(espn_id)
    except Exception as e:
        logger.warning(f"Could not fetch all players: {e}")

    return all_players


def convert_players(espn_league: ESPNLeague) -> list[Player]:
    """Convert all ESPN players to Player models"""
    players = []
    seen_players = set()

    # Get all available players (rostered + free agents)
    all_espn_players = get_all_players(espn_league)

    for espn_player in all_espn_players:
        try:
            espn_id = str(getattr(espn_player, "playerId", ""))
            if espn_id and espn_id not in seen_players:
                players.append(convert_player(espn_player))
                seen_players.add(espn_id)
        except Exception as e:
            logger.warning(f"Failed to convert player: {e}")
            continue

    return players


def convert_roster_entries(
    espn_league: ESPNLeague,
    team_mapping: dict[str, str],
    player_mapping: dict[str, str],
) -> list[RosterEntry]:
    """Convert ESPN roster data to RosterEntry models"""
    roster_entries = []

    for espn_team in espn_league.teams:
        team_id = str(espn_team.team_id)
        fantasy_team_id = team_mapping.get(team_id)

        if not fantasy_team_id:
            continue

        for espn_player in espn_team.roster:
            try:
                espn_player_id = str(getattr(espn_player, "playerId", ""))
                player_id = player_mapping.get(espn_player_id)

                if player_id:
                    # Determine if player is starting (simplified logic)
                    is_starting = getattr(espn_player, "lineupSlotId", 0) != 20  # 20 = bench

                    roster_entries.append(
                        RosterEntry(
                            fantasy_team_id=fantasy_team_id,
                            player_id=player_id,
                            is_starting=is_starting,
                            acquisition_type=AcquisitionType.FREE_AGENT,  # ESPN doesn't provide this
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to convert roster entry: {e}")
                continue

    return roster_entries


def convert_matchup(espn_matchup: Any, team_mapping: dict[str, str]) -> FantasyMatchup | None:
    """Convert ESPN matchup to FantasyMatchup model"""
    try:
        # Extract matchup data from ESPN object
        week = getattr(espn_matchup, "scoringPeriodId", 1)
        home_team_id = str(getattr(espn_matchup.home_team, "team_id", ""))
        away_team_id = str(getattr(espn_matchup.away_team, "team_id", ""))

        # Map to our team IDs
        home_fantasy_team_id = team_mapping.get(home_team_id)
        away_fantasy_team_id = team_mapping.get(away_team_id)

        if not home_fantasy_team_id or not away_fantasy_team_id:
            return None

        home_score = getattr(espn_matchup, "home_score", 0.0)
        away_score = getattr(espn_matchup, "away_score", 0.0)

        # Determine winner
        winner_id = None
        if home_score > away_score:
            winner_id = home_fantasy_team_id
        elif away_score > home_score:
            winner_id = away_fantasy_team_id

        return FantasyMatchup(
            week=week,
            home_team_id=home_fantasy_team_id,
            away_team_id=away_fantasy_team_id,
            home_score=home_score,
            away_score=away_score,
            winner_id=winner_id,
            is_playoff=getattr(espn_matchup, "is_playoff", False),
        )
    except Exception as e:
        logger.warning(f"Failed to convert matchup: {e}")
        return None


def convert_matchups(espn_league: ESPNLeague, team_mapping: dict[str, str]) -> list[FantasyMatchup]:
    """Convert all ESPN matchups to FantasyMatchup models"""
    matchups = []
    # Try to get all weeks up to the current week
    try:
        current_week = getattr(espn_league, "nfl_week", 1)
    except Exception:
        current_week = 1
    for week in range(1, current_week + 1):
        try:
            week_matchups = espn_league.scoreboard(week)
            for espn_matchup in week_matchups:
                matchup = convert_matchup(espn_matchup, team_mapping)
                if matchup:
                    matchups.append(matchup)
        except Exception as e:
            logger.warning(f"Failed to get matchups for week {week}: {e}")
            continue
    return matchups


def get_league_data(
    league_id: int, year: int
) -> tuple[LeagueConfig, list[FantasyTeam], list[Player], list[RosterEntry], list[FantasyMatchup]]:
    """Get complete league data and convert to our models"""
    try:
        # Fetch league data using espn_api
        espn_league = ESPNLeague(league_id=league_id, year=year)

        # Convert to our models
        league_config = convert_league_config(espn_league)
        teams = convert_teams(espn_league)
        players = convert_players(espn_league)

        # Create mappings for roster and matchup conversion
        team_mapping = {team.platform_team_id: team.id for team in teams}
        player_mapping = {player.espn_id: player.id for player in players if player.espn_id}

        roster_entries = convert_roster_entries(espn_league, team_mapping, player_mapping)
        matchups = convert_matchups(espn_league, team_mapping)

        return league_config, teams, players, roster_entries, matchups

    except Exception as e:
        raise ESPNAdapterError(f"Failed to get league data:") from e


def validate_league_access(league_id: int, year: int) -> bool:
    """Validate that we can access the league data"""
    try:
        espn_league = ESPNLeague(league_id=league_id, year=year)
        return len(espn_league.teams) > 0
    except Exception as e:
        logger.warning(f"Failed to access league {league_id}: {e}")
        return False


def get_weekly_matchups(league_id: int, year: int, week: int) -> list[FantasyMatchup]:
    """Get matchups for a specific week"""
    try:
        espn_league = ESPNLeague(league_id=league_id, year=year)

        # Convert teams for mapping
        teams = convert_teams(espn_league)
        team_mapping = {team.platform_team_id: team.id for team in teams}

        # Use scoreboard for the specific week
        week_matchups = []
        for espn_matchup in espn_league.scoreboard(week):
            matchup = convert_matchup(espn_matchup, team_mapping)
            if matchup:
                week_matchups.append(matchup)

        return week_matchups

    except Exception as e:
        raise ESPNAdapterError(f"Failed to get weekly matchups: {e}")


def main() -> None:
    """Example usage of ESPN adapter"""
    try:
        # Test league access
        league_id = 24481082
        year = 2024

        if validate_league_access(league_id, year):
            logger.info(f"Successfully accessed league {league_id}")

            # Get complete league data
            league_config, teams, players, rosters, matchups = get_league_data(league_id, year)

            logger.info(f"League: {league_config.league_name}")
            logger.info(f"Teams: {len(teams)}")
            logger.info(f"Players: {len(players)}")
            logger.info(f"Roster Entries: {len(rosters)}")
            logger.info(f"Matchups: {len(matchups)}")

        else:
            logger.error(f"Could not access league {league_id}")

    except ESPNAdapterError as e:
        logger.error(f"ESPN adapter error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
