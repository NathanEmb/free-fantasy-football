-- Fantasy Football Analysis Database Schema (SQLite)
-- This schema supports comprehensive fantasy football analysis for a single league including:
-- - Player and team data
-- - Roster management
-- - Historical statistics and projections
-- - Trade analysis and recommendations
-- - Matchup analysis and predictions

-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

-- NFL Teams
CREATE TABLE nfl_teams (
    id TEXT PRIMARY KEY,
    team_code TEXT UNIQUE NOT NULL, -- e.g., 'NE', 'GB'
    team_name TEXT NOT NULL, -- e.g., 'New England Patriots'
    city TEXT NOT NULL,
    conference TEXT NOT NULL, -- 'AFC' or 'NFC'
    division TEXT NOT NULL, -- 'East', 'West', 'North', 'South'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Players
CREATE TABLE players (
    id TEXT PRIMARY KEY,
    nfl_team_id TEXT REFERENCES nfl_teams(id),
    espn_id TEXT UNIQUE, -- ESPN player ID for data sync
    name TEXT NOT NULL,
    position TEXT NOT NULL, -- 'QB', 'RB', 'WR', 'TE', 'K', 'DEF'
    jersey_number INTEGER,
    height TEXT, -- e.g., '6-2'
    weight INTEGER, -- in pounds
    age INTEGER,
    experience_years INTEGER,
    college TEXT,
    is_active INTEGER DEFAULT 1, -- SQLite boolean as integer
    is_injured INTEGER DEFAULT 0, -- SQLite boolean as integer
    injury_status TEXT, -- 'Questionable', 'Doubtful', 'Out', etc.
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- League Configuration (Single League)
CREATE TABLE league_config (
    id TEXT PRIMARY KEY,
    league_name TEXT NOT NULL,
    platform TEXT, -- 'ESPN', 'Yahoo', 'Sleeper', 'Custom'
    platform_league_id TEXT, -- External platform league ID
    season_year INTEGER NOT NULL,
    scoring_type TEXT DEFAULT 'PPR', -- 'Standard', 'PPR', 'Half-PPR'
    team_count INTEGER,
    playoff_teams INTEGER,
    is_active INTEGER DEFAULT 1, -- SQLite boolean as integer
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Fantasy Teams
CREATE TABLE fantasy_teams (
    id TEXT PRIMARY KEY,
    owner_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    platform_team_id TEXT, -- External platform team ID
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    points_for REAL DEFAULT 0,
    points_against REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROSTER MANAGEMENT
-- ============================================================================

-- Roster Positions (defines roster structure)
CREATE TABLE roster_positions (
    id TEXT PRIMARY KEY,
    position TEXT NOT NULL, -- 'QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'FLEX', 'SUPERFLEX'
    count INTEGER NOT NULL, -- number of slots for this position
    is_bench INTEGER DEFAULT 0, -- SQLite boolean as integer
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Roster Entries (actual players on teams)
CREATE TABLE roster_entries (
    id TEXT PRIMARY KEY,
    fantasy_team_id TEXT REFERENCES fantasy_teams(id),
    player_id TEXT REFERENCES players(id),
    roster_position_id TEXT REFERENCES roster_positions(id),
    is_starting INTEGER DEFAULT 0, -- SQLite boolean as integer
    acquired_date TEXT, -- SQLite date as text
    acquisition_type TEXT, -- 'Draft', 'Waiver', 'Trade', 'Free Agent'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STATISTICS AND PERFORMANCE
-- ============================================================================

-- NFL Games/Events
CREATE TABLE nfl_games (
    id TEXT PRIMARY KEY,
    season_year INTEGER NOT NULL,
    week INTEGER NOT NULL,
    home_team_id TEXT REFERENCES nfl_teams(id),
    away_team_id TEXT REFERENCES nfl_teams(id),
    game_date TEXT, -- SQLite datetime as text
    home_score INTEGER,
    away_score INTEGER,
    game_status TEXT DEFAULT 'Scheduled', -- 'Scheduled', 'In Progress', 'Final'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Player Game Statistics
CREATE TABLE player_game_stats (
    id TEXT PRIMARY KEY,
    player_id TEXT REFERENCES players(id),
    nfl_game_id TEXT REFERENCES nfl_games(id),
    passing_yards INTEGER DEFAULT 0,
    passing_touchdowns INTEGER DEFAULT 0,
    passing_interceptions INTEGER DEFAULT 0,
    rushing_yards INTEGER DEFAULT 0,
    rushing_touchdowns INTEGER DEFAULT 0,
    receiving_yards INTEGER DEFAULT 0,
    receiving_touchdowns INTEGER DEFAULT 0,
    receptions INTEGER DEFAULT 0,
    targets INTEGER DEFAULT 0,
    fumbles_lost INTEGER DEFAULT 0,
    field_goals_made INTEGER DEFAULT 0,
    field_goals_attempted INTEGER DEFAULT 0,
    extra_points_made INTEGER DEFAULT 0,
    extra_points_attempted INTEGER DEFAULT 0,
    fantasy_points REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Team Defense Game Statistics
CREATE TABLE team_defense_game_stats (
    id TEXT PRIMARY KEY,
    nfl_team_id TEXT REFERENCES nfl_teams(id),
    nfl_game_id TEXT REFERENCES nfl_games(id),
    sacks INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    fumbles_recovered INTEGER DEFAULT 0,
    safeties INTEGER DEFAULT 0,
    touchdowns INTEGER DEFAULT 0,
    points_allowed INTEGER DEFAULT 0,
    yards_allowed INTEGER DEFAULT 0,
    fantasy_points REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FANTASY MATCHUPS AND SCORING
-- ============================================================================

-- Fantasy Matchups
CREATE TABLE fantasy_matchups (
    id TEXT PRIMARY KEY,
    week INTEGER NOT NULL,
    home_team_id TEXT REFERENCES fantasy_teams(id),
    away_team_id TEXT REFERENCES fantasy_teams(id),
    home_score REAL DEFAULT 0,
    away_score REAL DEFAULT 0,
    winner_id TEXT REFERENCES fantasy_teams(id),
    is_playoff INTEGER DEFAULT 0, -- SQLite boolean as integer
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Fantasy Team Weekly Scores
CREATE TABLE fantasy_team_weekly_scores (
    id TEXT PRIMARY KEY,
    fantasy_team_id TEXT REFERENCES fantasy_teams(id),
    week INTEGER NOT NULL,
    total_score REAL DEFAULT 0,
    bench_score REAL DEFAULT 0,
    optimal_score REAL DEFAULT 0, -- Best possible lineup
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PROJECTIONS AND ANALYSIS
-- ============================================================================

-- Player Projections
CREATE TABLE player_projections (
    id TEXT PRIMARY KEY,
    player_id TEXT REFERENCES players(id),
    week INTEGER NOT NULL,
    season_year INTEGER NOT NULL,
    source TEXT NOT NULL, -- 'ESPN', 'Yahoo', 'Custom', 'Algorithm'
    projected_fantasy_points REAL,
    projected_passing_yards INTEGER,
    projected_passing_touchdowns INTEGER,
    projected_rushing_yards INTEGER,
    projected_rushing_touchdowns INTEGER,
    projected_receiving_yards INTEGER,
    projected_receiving_touchdowns INTEGER,
    projected_receptions INTEGER,
    confidence_rating INTEGER, -- 1-10 scale
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Player Rankings
CREATE TABLE player_rankings (
    id TEXT PRIMARY KEY,
    player_id TEXT REFERENCES players(id),
    position TEXT NOT NULL,
    week INTEGER,
    season_year INTEGER,
    source TEXT NOT NULL,
    rank INTEGER NOT NULL,
    tier INTEGER, -- Tier grouping (1, 2, 3, etc.)
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TRADE ANALYSIS
-- ============================================================================

-- Trade Proposals
CREATE TABLE trade_proposals (
    id TEXT PRIMARY KEY,
    proposing_team_id TEXT REFERENCES fantasy_teams(id),
    receiving_team_id TEXT REFERENCES fantasy_teams(id),
    status TEXT DEFAULT 'Pending', -- 'Pending', 'Accepted', 'Rejected', 'Expired'
    proposed_date TEXT DEFAULT CURRENT_TIMESTAMP,
    response_date TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Trade Items (players/picks involved in trades)
CREATE TABLE trade_items (
    id TEXT PRIMARY KEY,
    trade_proposal_id TEXT REFERENCES trade_proposals(id),
    team_id TEXT REFERENCES fantasy_teams(id), -- Team giving up this item
    player_id TEXT REFERENCES players(id), -- NULL for draft picks
    draft_round INTEGER, -- For draft picks
    draft_pick_year INTEGER, -- For draft picks
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Trade Analysis Results
CREATE TABLE trade_analysis (
    id TEXT PRIMARY KEY,
    trade_proposal_id TEXT REFERENCES trade_proposals(id),
    team_a_value REAL, -- Fantasy value gained/lost
    team_b_value REAL,
    team_a_roster_improvement REAL, -- Percentage improvement
    team_b_roster_improvement REAL,
    analysis_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WAIVER WIRE AND FREE AGENTS
-- ============================================================================

-- Waiver Wire Priority
CREATE TABLE waiver_priorities (
    id TEXT PRIMARY KEY,
    fantasy_team_id TEXT REFERENCES fantasy_teams(id),
    priority_order INTEGER NOT NULL,
    season_year INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Free Agent Recommendations
CREATE TABLE free_agent_recommendations (
    id TEXT PRIMARY KEY,
    player_id TEXT REFERENCES players(id),
    week INTEGER NOT NULL,
    recommendation_reason TEXT,
    priority_level INTEGER, -- 1-5 scale
    projected_roster_impact REAL, -- Percentage improvement
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Player indexes
CREATE INDEX idx_players_position ON players(position);
CREATE INDEX idx_players_team ON players(nfl_team_id);
CREATE INDEX idx_players_active ON players(is_active);

-- Statistics indexes
CREATE INDEX idx_player_stats_player_week ON player_game_stats(player_id, nfl_game_id);
CREATE INDEX idx_player_stats_week ON player_game_stats(nfl_game_id);

-- Fantasy indexes
CREATE INDEX idx_roster_entries_team ON roster_entries(fantasy_team_id);
CREATE INDEX idx_fantasy_matchups_week ON fantasy_matchups(week);

-- Projections indexes
CREATE INDEX idx_projections_player_week ON player_projections(player_id, week, season_year);
CREATE INDEX idx_rankings_position_week ON player_rankings(position, week, season_year);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- SQLite doesn't support the same trigger syntax as PostgreSQL, so we'll handle this in the application layer
-- The updated_at field will be managed by the Python models 