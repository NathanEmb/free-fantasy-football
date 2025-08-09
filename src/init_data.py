"""
Database initialization script to populate sample data
"""

import uuid
from datetime import datetime

from .database import execute_insert, get_db_connection
from .logging_config import get_logger


def init_sample_data():
    """Initialize the database with sample data"""
    logger = get_logger(__name__)
    logger.info("Initializing sample data...")

    with get_db_connection() as conn:
        # Insert NFL Teams
        nfl_teams = [
            ("NE", "New England Patriots", "Boston", "AFC", "East"),
            ("BUF", "Buffalo Bills", "Buffalo", "AFC", "East"),
            ("MIA", "Miami Dolphins", "Miami", "AFC", "East"),
            ("NYJ", "New York Jets", "New York", "AFC", "East"),
            ("BAL", "Baltimore Ravens", "Baltimore", "AFC", "North"),
            ("CIN", "Cincinnati Bengals", "Cincinnati", "AFC", "North"),
            ("CLE", "Cleveland Browns", "Cleveland", "AFC", "North"),
            ("PIT", "Pittsburgh Steelers", "Pittsburgh", "AFC", "North"),
            ("HOU", "Houston Texans", "Houston", "AFC", "South"),
            ("IND", "Indianapolis Colts", "Indianapolis", "AFC", "South"),
            ("JAX", "Jacksonville Jaguars", "Jacksonville", "AFC", "South"),
            ("TEN", "Tennessee Titans", "Nashville", "AFC", "South"),
            ("DEN", "Denver Broncos", "Denver", "AFC", "West"),
            ("KC", "Kansas City Chiefs", "Kansas City", "AFC", "West"),
            ("LV", "Las Vegas Raiders", "Las Vegas", "AFC", "West"),
            ("LAC", "Los Angeles Chargers", "Los Angeles", "AFC", "West"),
            ("DAL", "Dallas Cowboys", "Dallas", "NFC", "East"),
            ("NYG", "New York Giants", "New York", "NFC", "East"),
            ("PHI", "Philadelphia Eagles", "Philadelphia", "NFC", "East"),
            ("WAS", "Washington Commanders", "Washington", "NFC", "East"),
            ("CHI", "Chicago Bears", "Chicago", "NFC", "North"),
            ("DET", "Detroit Lions", "Detroit", "NFC", "North"),
            ("GB", "Green Bay Packers", "Green Bay", "NFC", "North"),
            ("MIN", "Minnesota Vikings", "Minneapolis", "NFC", "North"),
            ("ATL", "Atlanta Falcons", "Atlanta", "NFC", "South"),
            ("CAR", "Carolina Panthers", "Charlotte", "NFC", "South"),
            ("NO", "New Orleans Saints", "New Orleans", "NFC", "South"),
            ("TB", "Tampa Bay Buccaneers", "Tampa Bay", "NFC", "South"),
            ("ARI", "Arizona Cardinals", "Phoenix", "NFC", "West"),
            ("LAR", "Los Angeles Rams", "Los Angeles", "NFC", "West"),
            ("SF", "San Francisco 49ers", "San Francisco", "NFC", "West"),
            ("SEA", "Seattle Seahawks", "Seattle", "NFC", "West"),
        ]

        for team_code, team_name, city, conference, division in nfl_teams:
            team_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO nfl_teams (id, team_code, team_name, city, conference, division)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (team_id, team_code, team_name, city, conference, division),
            )

        # Insert League Configuration
        league_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO league_config (id, league_name, platform, season_year, scoring_type, team_count, playoff_teams)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (league_id, "Sample Fantasy League", "ESPN", 2024, "PPR", 12, 6),
        )

        # Insert Fantasy Teams
        fantasy_teams = [
            ("John Smith", "The Smith Squad"),
            ("Sarah Johnson", "Johnson's Jets"),
            ("Mike Davis", "Davis Dynasty"),
            ("Lisa Wilson", "Wilson Warriors"),
            ("Tom Brown", "Brown's Brigade"),
            ("Amy Garcia", "Garcia's Giants"),
            ("David Miller", "Miller's Men"),
            ("Jennifer Taylor", "Taylor's Titans"),
            ("Robert Anderson", "Anderson's Army"),
            ("Maria Martinez", "Martinez's Mavens"),
            ("James Thompson", "Thompson's Team"),
            ("Patricia White", "White's Warriors"),
        ]

        team_ids = []
        # Add some realistic stats for the teams
        team_stats = [
            # (wins, losses, ties, points_for, points_against)
            (10, 4, 0, 2150.5, 1950.2),  # Strong team
            (9, 5, 0, 2089.3, 1980.1),   # Good team 
            (8, 6, 0, 2006.1, 2010.5),   # Above average
            (8, 6, 0, 1995.8, 1990.3),   # Above average
            (7, 7, 0, 1952.4, 2020.7),   # Average
            (7, 7, 0, 1948.2, 2055.9),   # Average
            (6, 8, 0, 1890.6, 2100.3),   # Below average
            (6, 8, 0, 1875.1, 2125.8),   # Below average
            (5, 9, 0, 1820.4, 2180.2),   # Poor team
            (5, 9, 0, 1805.7, 2195.6),   # Poor team
            (4, 10, 0, 1750.8, 2250.4),  # Weak team
            (3, 11, 0, 1695.2, 2305.9),  # Worst team
        ]
        
        for i, (owner_name, team_name) in enumerate(fantasy_teams):
            team_id = str(uuid.uuid4())
            team_ids.append(team_id)
            wins, losses, ties, points_for, points_against = team_stats[i]
            
            conn.execute(
                """
                INSERT INTO fantasy_teams (id, owner_name, team_name, platform_team_id, wins, losses, ties, points_for, points_against)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (team_id, owner_name, team_name, str(i + 1), wins, losses, ties, points_for, points_against),
            )

        # Insert Roster Positions
        roster_positions = [
            ("QB", 1, 0),
            ("RB", 2, 0),
            ("WR", 2, 0),
            ("TE", 1, 0),
            ("FLEX", 1, 0),
            ("K", 1, 0),
            ("DEF", 1, 0),
            ("BN", 6, 1),  # Bench positions
        ]

        for position, count, is_bench in roster_positions:
            position_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO roster_positions (id, position, count, is_bench)
                VALUES (?, ?, ?, ?)
            """,
                (position_id, position, count, is_bench),
            )

        # Insert Sample Players - Expanded pool to support 12 teams
        sample_players = [
            # QBs (need 12+ for each team)
            ("Patrick Mahomes", "QB", "KC"),
            ("Josh Allen", "QB", "BUF"),
            ("Lamar Jackson", "QB", "BAL"),
            ("Jalen Hurts", "QB", "PHI"),
            ("Justin Herbert", "QB", "LAC"),
            ("Tua Tagovailoa", "QB", "MIA"),
            ("Dak Prescott", "QB", "DAL"),
            ("Kirk Cousins", "QB", "MIN"),
            ("Geno Smith", "QB", "SEA"),
            ("Derek Carr", "QB", "NO"),
            ("Daniel Jones", "QB", "NYG"),
            ("Russell Wilson", "QB", "DEN"),
            ("Aaron Rodgers", "QB", "NYJ"),
            ("Trevor Lawrence", "QB", "JAX"),
            ("Kyler Murray", "QB", "ARI"),
            # RBs (need 24+ for 2 per team)
            ("Christian McCaffrey", "RB", "SF"),
            ("Saquon Barkley", "RB", "PHI"),
            ("Derrick Henry", "RB", "BAL"),
            ("Nick Chubb", "RB", "CLE"),
            ("Austin Ekeler", "RB", "WAS"),
            ("Alvin Kamara", "RB", "NO"),
            ("Joe Mixon", "RB", "HOU"),
            ("Rachaad White", "RB", "TB"),
            ("Breece Hall", "RB", "NYJ"),
            ("Travis Etienne", "RB", "JAX"),
            ("Kenneth Walker", "RB", "SEA"),
            ("Tony Pollard", "RB", "TEN"),
            ("D'Andre Swift", "RB", "CHI"),
            ("Najee Harris", "RB", "PIT"),
            ("Javonte Williams", "RB", "DEN"),
            ("James Cook", "RB", "BUF"),
            ("Rhamondre Stevenson", "RB", "NE"),
            ("Josh Jacobs", "RB", "GB"),
            ("Isiah Pacheco", "RB", "KC"),
            ("Bijan Robinson", "RB", "ATL"),
            ("De'Von Achane", "RB", "MIA"),
            ("Kyren Williams", "RB", "LAR"),
            ("David Montgomery", "RB", "DET"),
            ("Jahmyr Gibbs", "RB", "DET"),
            ("Alexander Mattison", "RB", "LV"),
            # WRs (need 24+ for 2 per team)
            ("Tyreek Hill", "WR", "MIA"),
            ("CeeDee Lamb", "WR", "DAL"),
            ("Amon-Ra St. Brown", "WR", "DET"),
            ("Stefon Diggs", "WR", "HOU"),
            ("Davante Adams", "WR", "LV"),
            ("AJ Brown", "WR", "PHI"),
            ("Cooper Kupp", "WR", "LAR"),
            ("Mike Evans", "WR", "TB"),
            ("DK Metcalf", "WR", "SEA"),
            ("Deebo Samuel", "WR", "SF"),
            ("Ja'Marr Chase", "WR", "CIN"),
            ("Puka Nacua", "WR", "LAR"),
            ("Keenan Allen", "WR", "CHI"),
            ("DeVonta Smith", "WR", "PHI"),
            ("Chris Olave", "WR", "NO"),
            ("Garrett Wilson", "WR", "NYJ"),
            ("Amari Cooper", "WR", "CLE"),
            ("Calvin Ridley", "WR", "TEN"),
            ("Terry McLaurin", "WR", "WAS"),
            ("DJ Moore", "WR", "CHI"),
            ("Tee Higgins", "WR", "CIN"),
            ("Jaylen Waddle", "WR", "MIA"),
            ("Michael Pittman", "WR", "IND"),
            ("Brandon Aiyuk", "WR", "SF"),
            ("Diontae Johnson", "WR", "PIT"),
            ("Tyler Lockett", "WR", "SEA"),
            # TEs (need 12+ for each team)
            ("Travis Kelce", "TE", "KC"),
            ("Sam LaPorta", "TE", "DET"),
            ("T.J. Hockenson", "TE", "MIN"),
            ("George Kittle", "TE", "SF"),
            ("Mark Andrews", "TE", "BAL"),
            ("Kyle Pitts", "TE", "ATL"),
            ("Evan Engram", "TE", "JAX"),
            ("Dallas Goedert", "TE", "PHI"),
            ("David Njoku", "TE", "CLE"),
            ("Jake Ferguson", "TE", "DAL"),
            ("Cole Kmet", "TE", "CHI"),
            ("Pat Freiermuth", "TE", "PIT"),
            ("Tyler Higbee", "TE", "LAR"),
            ("Dalton Schultz", "TE", "HOU"),
            # Kickers (need 12+ for each team)
            ("Justin Tucker", "K", "BAL"),
            ("Harrison Butker", "K", "KC"),
            ("Evan McPherson", "K", "CIN"),
            ("Younghoe Koo", "K", "ATL"),
            ("Tyler Bass", "K", "BUF"),
            ("Daniel Carlson", "K", "LV"),
            ("Jake Moody", "K", "SF"),
            ("Brandon McManus", "K", "WAS"),
            ("Chris Boswell", "K", "PIT"),
            ("Cameron Dicker", "K", "LAC"),
            ("Matt Gay", "K", "IND"),
            ("Greg Zuerlein", "K", "NYJ"),
            ("Jason Sanders", "K", "MIA"),
            # DEF/ST (need 12+ for each team)
            ("San Francisco 49ers", "DEF", "SF"),
            ("Dallas Cowboys", "DEF", "DAL"),
            ("Baltimore Ravens", "DEF", "BAL"),
            ("Buffalo Bills", "DEF", "BUF"),
            ("Philadelphia Eagles", "DEF", "PHI"),
            ("Pittsburgh Steelers", "DEF", "PIT"),
            ("Cleveland Browns", "DEF", "CLE"),
            ("Miami Dolphins", "DEF", "MIA"),
            ("Kansas City Chiefs", "DEF", "KC"),
            ("New York Jets", "DEF", "NYJ"),
            ("Denver Broncos", "DEF", "DEN"),
            ("New Orleans Saints", "DEF", "NO"),
            ("Seattle Seahawks", "DEF", "SEA"),
        ]

        # Get team IDs for player insertion
        team_id_map = {}
        cursor = conn.execute("SELECT id, team_code FROM nfl_teams")
        for row in cursor.fetchall():
            team_id_map[row["team_code"]] = row["id"]

        player_ids = []
        for player_name, position, team_code in sample_players:
            player_id = str(uuid.uuid4())
            player_ids.append(player_id)
            nfl_team_id = team_id_map.get(team_code)

            conn.execute(
                """
                INSERT INTO players (id, nfl_team_id, name, position, is_active)
                VALUES (?, ?, ?, ?, ?)
            """,
                (player_id, nfl_team_id, player_name, position, 1),
            )

        # Insert roster entries using round-robin distribution to ensure all teams get players
        # Group players by position for fair distribution
        players_by_position = {}
        for i, (player_name, position, team_code) in enumerate(sample_players):
            if position not in players_by_position:
                players_by_position[position] = []
            players_by_position[position].append(player_ids[i])
        
        # Define roster requirements per team
        roster_requirements = [
            ("QB", 1),    # 1 QB per team
            ("RB", 2),    # 2 RBs per team  
            ("WR", 2),    # 2 WRs per team
            ("TE", 1),    # 1 TE per team
            ("K", 1),     # 1 K per team
            ("DEF", 1),   # 1 DEF per team
        ]
        
        # Distribute players to teams using round-robin
        for position, count_needed in roster_requirements:
            if position in players_by_position:
                available_players = players_by_position[position]
                
                # Distribute players round-robin style
                for team_index, team_id in enumerate(team_ids):
                    for slot in range(count_needed):
                        # Calculate which player to assign using round-robin
                        player_index = (team_index * count_needed + slot) % len(available_players)
                        player_id = available_players[player_index]
                        
                        # Get roster position ID
                        cursor = conn.execute(
                            "SELECT id FROM roster_positions WHERE position = ?", (position,)
                        )
                        roster_position_row = cursor.fetchone()
                        if roster_position_row:
                            roster_position_id = roster_position_row["id"]
                            roster_entry_id = str(uuid.uuid4())
                            
                            conn.execute(
                                """
                                INSERT INTO roster_entries (id, fantasy_team_id, player_id, roster_position_id, is_starting)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                                (roster_entry_id, team_id, player_id, roster_position_id, 1),
                            )

        conn.commit()
        
        # Log roster distribution for verification
        total_roster_entries = 0
        for team_id in team_ids:
            cursor = conn.execute("SELECT COUNT(*) as count FROM roster_entries WHERE fantasy_team_id = ?", (team_id,))
            count = cursor.fetchone()["count"]
            total_roster_entries += count
        
        logger.info(
            f"Initialized database with {len(nfl_teams)} NFL teams, {len(sample_players)} players, and {len(fantasy_teams)} fantasy teams"
        )
        logger.info(f"Total roster entries created: {total_roster_entries} (average {total_roster_entries/len(team_ids):.1f} per team)")
        
        # Verify each team has players
        teams_with_players = 0
        for team_id in team_ids:
            cursor = conn.execute("SELECT COUNT(*) as count FROM roster_entries WHERE fantasy_team_id = ?", (team_id,))
            count = cursor.fetchone()["count"]
            if count > 0:
                teams_with_players += 1
        
        logger.info(f"Teams with players: {teams_with_players}/{len(team_ids)}")
        if teams_with_players < len(team_ids):
            logger.warning(f"{len(team_ids) - teams_with_players} teams have no players assigned!")


if __name__ == "__main__":
    init_sample_data()
