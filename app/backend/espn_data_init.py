"""
ESPN Data Initialization

This module initializes the database with real data from ESPN using the espn_adapter.
"""

import os
import uuid
from typing import Optional

from database import execute_query, get_db_connection
from espn_adapter import ESPNAdapterError, get_league_data, validate_league_access


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


def init_espn_data():
    """Initialize the database with ESPN data"""
    print("Initializing database with ESPN data...")

    league_id, year = get_league_config_from_env()
    print(f"Using ESPN League ID: {league_id}, Year: {year}")

    # Validate league access first
    if not validate_league_access(league_id, year):
        print(f"Could not access ESPN league {league_id} for year {year}")
        print("Please check your ESPN_LEAGUE_ID and ESPN_YEAR environment variables")
        return False

    try:
        # Get data from ESPN
        league_config, teams, players, roster_entries, matchups = get_league_data(league_id, year)

        with get_db_connection() as conn:
            # Clear existing data (optional - you might want to keep existing data)
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

            # Insert fantasy teams
            team_mapping = {}  # ESPN team ID -> database team ID
            for team in teams:
                team_db_id = str(uuid.uuid4())
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

            # Insert players
            player_mapping = {}  # ESPN player ID -> database player ID
            for player in players:
                player_db_id = str(uuid.uuid4())
                if player.espn_id:
                    player_mapping[player.espn_id] = player_db_id

                conn.execute(
                    """
                    INSERT INTO players (id, espn_id, name, position, nfl_team_id, jersey_number, height, weight, age, experience_years, college, is_injured, injury_status, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        player_db_id,
                        player.espn_id,
                        player.name,
                        safe_enum_value(player.position),
                        player.nfl_team_id,
                        player.jersey_number,
                        player.height,
                        player.weight,
                        player.age,
                        player.experience_years,
                        player.college,
                        1 if player.is_injured else 0,
                        player.injury_status,
                        1 if player.is_active else 0,
                    ),
                )

            # Insert roster entries
            for roster_entry in roster_entries:
                roster_db_id = str(uuid.uuid4())
                fantasy_team_id = team_mapping.get(roster_entry.fantasy_team_id)
                player_id = player_mapping.get(roster_entry.player_id)

                if fantasy_team_id and player_id:
                    # Get or create a default roster position
                    position_value = (
                        safe_enum_value(roster_entry.position) if roster_entry.position else "BN"
                    )
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
                home_team_id = team_mapping.get(matchup.home_team_id)
                away_team_id = team_mapping.get(matchup.away_team_id)
                winner_id = team_mapping.get(matchup.winner_id) if matchup.winner_id else None

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
            print(f"Successfully initialized database with ESPN data:")
            print(f"  - League: {league_config.league_name}")
            print(f"  - Teams: {len(teams)}")
            print(f"  - Players: {len(players)}")
            print(f"  - Roster Entries: {len(roster_entries)}")
            print(f"  - Matchups: {len(matchups)}")
            return True

    except ESPNAdapterError as e:
        print(f"ESPN adapter error: {e}")
        return False
    except Exception as e:
        print(f"Error initializing ESPN data: {e}")
        return False


if __name__ == "__main__":
    init_espn_data()
