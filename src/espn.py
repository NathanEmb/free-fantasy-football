"""
ESPN Integration Module

This module provides a unified interface for interacting with ESPN fantasy football data,
including API access, data conversion, and database operations.
"""

import logging
import os
import uuid
from typing import Any

from espn_api.football import League as ESPNLeague
from espn_api.football import Player as ESPNPlayer
from espn_api.football import Team as ESPNTeam

from src.database import get_db_connection
from src.logging_config import get_logger
from src.models import (
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

logger = get_logger(__name__)


class ESPNFantasyError(Exception):
    """Custom exception for ESPN fantasy football errors"""

    pass


def get_league_config_from_env() -> tuple[int, int]:
    """Get league configuration from environment variables"""
    league_id = int(os.getenv("ESPN_LEAGUE_ID", "24481082"))
    year = int(os.getenv("ESPN_YEAR", "2024"))
    return league_id, year


def safe_enum_value(enum_obj) -> str:
    """Safely get enum value as string"""
    if enum_obj is None:
        return None
    if hasattr(enum_obj, "value"):
        return str(enum_obj.value)
    return str(enum_obj)


def determine_scoring_type(espn_league: ESPNLeague) -> ScoringType:
    """Determine scoring type from ESPN league settings"""
    try:
        if hasattr(espn_league.settings, "scoring_settings"):
            scoring = espn_league.settings.scoring_settings
            if hasattr(scoring, "reception") and scoring.reception == 1.0:
                return ScoringType.PPR
            elif hasattr(scoring, "reception") and scoring.reception == 0.5:
                return ScoringType.HALF_PPR
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
        raise ESPNFantasyError(f"Failed to convert league config: {e}")


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
        raise ESPNFantasyError(f"Failed to convert team {espn_team.team_name}: {e}")


def convert_teams(espn_league: ESPNLeague) -> list[FantasyTeam]:
    """Convert all ESPN teams to FantasyTeam models"""
    teams = []
    try:
        for espn_team in espn_league.teams:
            try:
                team = convert_team(espn_team)
                teams.append(team)
            except Exception as e:
                logger.warning(f"Skipping team conversion: {e}")
                continue
    except Exception as e:
        logger.error(f"Failed to access teams: {e}")
    return teams


def convert_player(espn_player: ESPNPlayer) -> Player:
    """Convert ESPN Player to Player model"""
    try:
        # Map position
        position = map_espn_position(espn_player.position)

        # Get team info
        nfl_team_id = None
        if hasattr(espn_player, "proTeamId") and espn_player.proTeamId:
            nfl_team_id = str(espn_player.proTeamId)

        # Get additional player info
        jersey_number = getattr(espn_player, "jersey", None)
        height = getattr(espn_player, "height", None)
        weight = getattr(espn_player, "weight", None)
        age = getattr(espn_player, "age", None)
        experience_years = getattr(espn_player, "experience", None)
        college = getattr(espn_player, "college", None)

        # Injury status
        is_injured = getattr(espn_player, "injured", False)
        injury_status = getattr(espn_player, "injuryStatus", None)

        # Handle case where injury_status is a list (defense/special teams)
        if isinstance(injury_status, list):
            injury_status = None if not injury_status else str(injury_status[0])

        # Active status
        is_active = getattr(espn_player, "active", True)

        return Player(
            name=espn_player.name,
            position=position,
            nfl_team_id=nfl_team_id,
            espn_id=str(espn_player.playerId),
            jersey_number=jersey_number,
            height=height,
            weight=weight,
            age=age,
            experience_years=experience_years,
            college=college,
            is_injured=1 if is_injured else 0,
            injury_status=injury_status,
            is_active=1 if is_active else 0,
        )
    except Exception as e:
        raise ESPNFantasyError(f"Failed to convert player {espn_player.name}: {e}")


def get_all_players(espn_league: ESPNLeague) -> list[ESPNPlayer]:
    """Get all players from ESPN league (rosters + free agents)"""
    all_players = []
    seen_player_ids = set()

    # Get players from team rosters
    for team in espn_league.teams:
        for player in team.roster:
            if str(player.playerId) not in seen_player_ids:
                all_players.append(player)
                seen_player_ids.add(str(player.playerId))

    # Get free agents if available (call as method)
    try:
        free_agents = espn_league.free_agents()
        for player in free_agents:
            if str(player.playerId) not in seen_player_ids:
                all_players.append(player)
                seen_player_ids.add(str(player.playerId))
    except Exception as e:
        logger.warning(f"Could not get free agents: {e}")

    return all_players


def convert_players(espn_league: ESPNLeague) -> list[Player]:
    """Convert all ESPN players to Player models"""
    players = []
    all_espn_players = get_all_players(espn_league)

    for espn_player in all_espn_players:
        try:
            player = convert_player(espn_player)
            players.append(player)
        except Exception as e:
            logger.warning(f"Skipping player conversion: {e}")
            continue

    return players


def convert_roster_entries(
    espn_league: ESPNLeague,
    team_mapping: dict[str, str],
    player_mapping: dict[str, str],
) -> list[RosterEntry]:
    """Convert ESPN roster entries to RosterEntry models"""
    roster_entries = []

    for team in espn_league.teams:
        fantasy_team_id = team_mapping.get(str(team.team_id))
        if not fantasy_team_id:
            continue

        for player in team.roster:
            player_id = player_mapping.get(str(player.playerId))
            if not player_id:
                continue

            # Determine if player is starting
            is_starting = getattr(player, "starter", False)

            # Determine acquisition type
            acquisition_type = AcquisitionType.FREE_AGENT
            if hasattr(player, "acquisitionType"):
                acquisition_type = player.acquisitionType

            # Create roster entry
            roster_entry = RosterEntry(
                fantasy_team_id=fantasy_team_id,
                player_id=player_id,
                is_starting=is_starting,
                acquisition_type=acquisition_type,
            )
            roster_entries.append(roster_entry)

    return roster_entries


def convert_matchup(
    espn_matchup: Any, team_mapping: dict[str, str], week: int = 1
) -> FantasyMatchup | None:
    """Convert ESPN matchup to FantasyMatchup model"""
    try:
        home_team_id = team_mapping.get(str(espn_matchup.home_team.team_id))
        away_team_id = team_mapping.get(str(espn_matchup.away_team.team_id))

        if not home_team_id or not away_team_id:
            return None

        # Determine winner
        winner_id = None
        if hasattr(espn_matchup, "winner"):
            winner_id = team_mapping.get(str(espn_matchup.winner.team_id))

        return FantasyMatchup(
            week=week,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=espn_matchup.home_score,
            away_score=espn_matchup.away_score,
            winner_id=winner_id,
            is_playoff=getattr(espn_matchup, "playoff", False),
        )
    except Exception as e:
        logger.warning(f"Failed to convert matchup: {e}")
        return None


def convert_matchups(espn_league: ESPNLeague, team_mapping: dict[str, str]) -> list[FantasyMatchup]:
    """Convert all ESPN matchups to FantasyMatchup models"""
    matchups = []

    # Get matchups from scoreboard
    try:
        for week in range(1, 18):  # Regular season weeks
            week_matchups = espn_league.scoreboard(week)
            for espn_matchup in week_matchups:
                matchup = convert_matchup(espn_matchup, team_mapping, week)
                if matchup:
                    matchups.append(matchup)
    except Exception as e:
        logger.warning(f"Failed to get matchups for week {week}: {e}")

    return matchups


def validate_league_access(league_id: int, year: int) -> bool:
    """Validate that we can access the league data"""
    try:
        espn_league = ESPNLeague(league_id=league_id, year=year)
        return len(espn_league.teams) > 0
    except Exception as e:
        logger.warning(f"Failed to access league {league_id}: {e}")
        return False


def get_league_data(
    league_id: int, year: int
) -> tuple[LeagueConfig, list[FantasyTeam], list[Player], list[RosterEntry], list[FantasyMatchup]]:
    """Get complete league data and convert to our models"""
    try:
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
        logger.error(f"Error in get_league_data: {e}")
        raise ESPNFantasyError(f"Failed to get league data: {e}")


def init_espn_data() -> bool:
    """Initialize the database with ESPN data"""
    logger.info("Initializing database with ESPN data...")

    league_id, year = get_league_config_from_env()
    logger.info(f"Using ESPN League ID: {league_id}, Year: {year}")

    # Validate league access first
    if not validate_league_access(league_id, year):
        logger.error(f"Could not access ESPN league {league_id} for year {year}")
        logger.error("Please check your ESPN_LEAGUE_ID and ESPN_YEAR environment variables")
        return False

    try:
        # Get data from ESPN
        league_config, teams, players, roster_entries, matchups = get_league_data(league_id, year)

        with get_db_connection() as conn:
            # Clear existing data
            conn.execute("DELETE FROM fantasy_matchups")
            conn.execute("DELETE FROM roster_entries")
            conn.execute("DELETE FROM players")
            conn.execute("DELETE FROM fantasy_teams")
            conn.execute("DELETE FROM league_config")

            # Insert league configuration
            league_db_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO league_config (id, league_name, platform, platform_league_id, season_year, scoring_type, team_count, playoff_teams)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    league_db_id,
                    league_config.league_name,
                    safe_enum_value(league_config.platform),
                    league_config.platform_league_id,
                    league_config.season_year,
                    safe_enum_value(league_config.scoring_type),
                    league_config.team_count,
                    league_config.playoff_teams,
                ),
            )

            # Insert fantasy teams - use the same UUIDs as in the models
            team_mapping = {}  # ESPN team ID -> database team ID
            for team in teams:
                team_db_id = team.id  # Use the UUID from the model, not a new one
                team_mapping[team.platform_team_id] = team_db_id

                conn.execute(
                    """
                    INSERT INTO fantasy_teams (id, owner_name, team_name, platform_team_id, wins, losses, ties, points_for, points_against)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        team_db_id,
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

            # Insert players - use the same UUIDs as in the models
            player_mapping = {}  # ESPN player ID -> database player ID
            for player in players:
                player_db_id = player.id  # Use the UUID from the model, not a new one
                if player.espn_id:  # Only add if espn_id exists
                    player_mapping[player.espn_id] = player_db_id

                # Debug: print the values being inserted
                values = (
                    player_db_id,
                    player.nfl_team_id,
                    player.name,
                    safe_enum_value(player.position),
                    player.espn_id,
                    player.jersey_number,
                    player.height,
                    player.weight,
                    player.age,
                    player.experience_years,
                    player.college,
                    1 if player.is_injured else 0,
                    player.injury_status,
                    1 if player.is_active else 0,
                )

                logger.debug(f"Inserting player {player.name}")

                conn.execute(
                    """
                    INSERT INTO players (id, nfl_team_id, name, position, espn_id, jersey_number, height, weight, age, experience_years, college, is_injured, injury_status, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )

            # Insert roster entries
            for roster_entry in roster_entries:
                roster_db_id = str(uuid.uuid4())
                fantasy_team_id = roster_entry.fantasy_team_id  # This is already the correct UUID
                player_id = roster_entry.player_id  # This is already the correct UUID

                if fantasy_team_id and player_id:
                    # Get or create a default roster position (use bench as default)
                    position_value = "BN"
                    cursor = conn.execute(
                        "SELECT id FROM roster_positions WHERE position = ?", (position_value,)
                    )
                    roster_position_row = cursor.fetchone()
                    if roster_position_row:
                        roster_position_id = roster_position_row["id"]
                    else:
                        # Create a default bench position if none exists
                        roster_position_id = str(uuid.uuid4())
                        conn.execute(
                            """
                            INSERT INTO roster_positions (id, position, count, is_bench)
                            VALUES (?, ?, ?, ?)
                            """,
                            (roster_position_id, "BN", 1, 1),
                        )

                    conn.execute(
                        """
                        INSERT INTO roster_entries (id, fantasy_team_id, player_id, roster_position_id, is_starting, acquisition_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            roster_db_id,
                            fantasy_team_id,
                            player_id,
                            roster_position_id,
                            1 if roster_entry.is_starting else 0,
                            safe_enum_value(roster_entry.acquisition_type)
                            if roster_entry.acquisition_type
                            else "Free Agent",
                        ),
                    )

            # Insert matchups
            for matchup in matchups:
                matchup_db_id = str(uuid.uuid4())
                home_team_id = matchup.home_team_id  # This is already the correct UUID
                away_team_id = matchup.away_team_id  # This is already the correct UUID
                winner_id = matchup.winner_id if matchup.winner_id else None  # This is already the correct UUID

                if home_team_id and away_team_id:
                    conn.execute(
                        """
                        INSERT INTO fantasy_matchups (id, week, home_team_id, away_team_id, home_score, away_score, winner_id, is_playoff)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            matchup_db_id,
                            matchup.week,
                            home_team_id,
                            away_team_id,
                            matchup.home_score,
                            matchup.away_score,
                            winner_id,
                            1 if matchup.is_playoff else 0,
                        ),
                    )

            conn.commit()
            logger.info(f"Successfully initialized database with ESPN data:")
            logger.info(f"  - League: {league_config.league_name}")
            logger.info(f"  - Teams: {len(teams)}")
            logger.info(f"  - Players: {len(players)}")
            logger.info(f"  - Roster Entries: {len(roster_entries)}")
            logger.info(f"  - Matchups: {len(matchups)}")
            return True

    except ESPNFantasyError as e:
        logger.error(f"ESPN fantasy error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error initializing ESPN data: {e}")
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
            matchup = convert_matchup(espn_matchup, team_mapping, week)
            if matchup:
                week_matchups.append(matchup)

        return week_matchups

    except Exception as e:
        raise ESPNFantasyError(f"Failed to get weekly matchups: {e}")


def main() -> None:
    """Example usage of ESPN integration"""
    try:
        league_id, year = get_league_config_from_env()

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

    except ESPNFantasyError as e:
        logger.error(f"ESPN fantasy error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
