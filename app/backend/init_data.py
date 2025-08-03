"""
Database initialization script to populate sample data
"""

import uuid
from datetime import datetime
from database import get_db_connection, execute_insert


def init_sample_data():
    """Initialize the database with sample data"""
    print("Initializing sample data...")
    
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
            conn.execute("""
                INSERT INTO nfl_teams (id, team_code, team_name, city, conference, division)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (team_id, team_code, team_name, city, conference, division))
        
        # Insert League Configuration
        league_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO league_config (id, league_name, platform, season_year, scoring_type, team_count, playoff_teams)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (league_id, "Sample Fantasy League", "ESPN", 2024, "PPR", 12, 6))
        
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
        for owner_name, team_name in fantasy_teams:
            team_id = str(uuid.uuid4())
            team_ids.append(team_id)
            conn.execute("""
                INSERT INTO fantasy_teams (id, owner_name, team_name)
                VALUES (?, ?, ?)
            """, (team_id, owner_name, team_name))
        
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
            conn.execute("""
                INSERT INTO roster_positions (id, position, count, is_bench)
                VALUES (?, ?, ?, ?)
            """, (position_id, position, count, is_bench))
        
        # Insert Sample Players
        sample_players = [
            # QBs
            ("Patrick Mahomes", "QB", "KC"),
            ("Josh Allen", "QB", "BUF"),
            ("Lamar Jackson", "QB", "BAL"),
            ("Jalen Hurts", "QB", "PHI"),
            ("Justin Herbert", "QB", "LAC"),
            # RBs
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
            # WRs
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
            # TEs
            ("Travis Kelce", "TE", "KC"),
            ("Sam LaPorta", "TE", "DET"),
            ("T.J. Hockenson", "TE", "MIN"),
            ("George Kittle", "TE", "SF"),
            ("Mark Andrews", "TE", "BAL"),
            # Ks
            ("Justin Tucker", "K", "BAL"),
            ("Harrison Butker", "K", "KC"),
            ("Evan McPherson", "K", "CIN"),
            ("Younghoe Koo", "K", "ATL"),
            ("Tyler Bass", "K", "BUF"),
            # DEFs
            ("San Francisco 49ers", "DEF", "SF"),
            ("Dallas Cowboys", "DEF", "DAL"),
            ("Baltimore Ravens", "DEF", "BAL"),
            ("Buffalo Bills", "DEF", "BUF"),
            ("Philadelphia Eagles", "DEF", "PHI"),
        ]
        
        # Get team IDs for player insertion
        team_id_map = {}
        cursor = conn.execute("SELECT id, team_code FROM nfl_teams")
        for row in cursor.fetchall():
            team_id_map[row['team_code']] = row['id']
        
        player_ids = []
        for player_name, position, team_code in sample_players:
            player_id = str(uuid.uuid4())
            player_ids.append(player_id)
            nfl_team_id = team_id_map.get(team_code)
            
            conn.execute("""
                INSERT INTO players (id, nfl_team_id, name, position, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (player_id, nfl_team_id, player_name, position, 1))
        
        # Insert some sample roster entries (assigning players to teams)
        for i, team_id in enumerate(team_ids):
            # Assign 1 QB, 2 RBs, 2 WRs, 1 TE, 1 K, 1 DEF to each team
            positions_needed = ["QB", "RB", "RB", "WR", "WR", "TE", "K", "DEF"]
            player_index = i * len(positions_needed)
            
            for j, position in enumerate(positions_needed):
                if player_index + j < len(player_ids):
                    player_id = player_ids[player_index + j]
                    roster_entry_id = str(uuid.uuid4())
                    
                    # Get roster position ID
                    cursor = conn.execute("SELECT id FROM roster_positions WHERE position = ?", (position,))
                    roster_position_row = cursor.fetchone()
                    if roster_position_row:
                        roster_position_id = roster_position_row['id']
                        
                        conn.execute("""
                            INSERT INTO roster_entries (id, fantasy_team_id, player_id, roster_position_id, is_starting)
                            VALUES (?, ?, ?, ?, ?)
                        """, (roster_entry_id, team_id, player_id, roster_position_id, 1))
        
        conn.commit()
        print(f"Initialized database with {len(nfl_teams)} NFL teams, {len(sample_players)} players, and {len(fantasy_teams)} fantasy teams")


if __name__ == "__main__":
    init_sample_data() 