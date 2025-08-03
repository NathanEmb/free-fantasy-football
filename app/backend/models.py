"""
Data models for Fantasy Football Analysis Database (SQLite)

These models represent the core entities in the fantasy football analysis system
and provide type safety and validation for database operations with SQLite.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class Position(Enum):
    """Player positions"""

    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"
    FLEX = "FLEX"
    SUPERFLEX = "SUPERFLEX"


class Conference(Enum):
    """NFL conferences"""

    AFC = "AFC"
    NFC = "NFC"


class Division(Enum):
    """NFL divisions"""

    EAST = "East"
    WEST = "West"
    NORTH = "North"
    SOUTH = "South"


class ScoringType(Enum):
    """Fantasy scoring types"""

    STANDARD = "Standard"
    PPR = "PPR"
    HALF_PPR = "Half-PPR"


class Platform(Enum):
    """Fantasy platforms"""

    ESPN = "ESPN"
    YAHOO = "Yahoo"
    SLEEPER = "Sleeper"
    CUSTOM = "Custom"


class AcquisitionType(Enum):
    """Player acquisition types"""

    DRAFT = "Draft"
    WAIVER = "Waiver"
    TRADE = "Trade"
    FREE_AGENT = "Free Agent"


class TradeStatus(Enum):
    """Trade proposal statuses"""

    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    EXPIRED = "Expired"


class GameStatus(Enum):
    """NFL game statuses"""

    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    FINAL = "Final"


@dataclass
class NFLTeam:
    """NFL team model"""

    team_code: str
    team_name: str
    city: str
    conference: Conference
    division: Division
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate team data"""
        if not self.team_code or len(self.team_code) > 3:
            raise ValueError("Team code must be 1-3 characters")
        if not self.team_name or len(self.team_name) > 50:
            raise ValueError("Team name must be 1-50 characters")
        if not self.city or len(self.city) > 30:
            raise ValueError("City must be 1-30 characters")


@dataclass
class Player:
    """Player model"""

    name: str
    position: Position
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nfl_team_id: str | None = None
    espn_id: str | None = None
    jersey_number: int | None = None
    height: str | None = None
    weight: int | None = None
    age: int | None = None
    experience_years: int | None = None
    college: str | None = None
    is_active: int = 1  # SQLite boolean as integer
    is_injured: int = 0  # SQLite boolean as integer
    injury_status: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate player data"""
        if not self.name or len(self.name) > 100:
            raise ValueError("Player name must be 1-100 characters")
        if self.jersey_number is not None and (self.jersey_number < 0 or self.jersey_number > 99):
            raise ValueError("Jersey number must be 0-99")
        if self.weight is not None and (self.weight < 100 or self.weight > 400):
            raise ValueError("Weight must be 100-400 pounds")
        if self.age is not None and (self.age < 18 or self.age > 50):
            raise ValueError("Age must be 18-50")
        if self.experience_years is not None and (
            self.experience_years < 0 or self.experience_years > 25
        ):
            raise ValueError("Experience years must be 0-25")


@dataclass
class LeagueConfig:
    """League configuration model"""

    league_name: str
    platform: Platform
    season_year: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    platform_league_id: str | None = None
    scoring_type: ScoringType = ScoringType.PPR
    team_count: int | None = None
    playoff_teams: int | None = None
    is_active: int = 1  # SQLite boolean as integer
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate league config data"""
        if not self.league_name or len(self.league_name) > 100:
            raise ValueError("League name must be 1-100 characters")
        if self.season_year < 2000 or self.season_year > 2030:
            raise ValueError("Season year must be 2000-2030")
        if self.team_count is not None and (self.team_count < 2 or self.team_count > 32):
            raise ValueError("Team count must be 2-32")
        if self.playoff_teams is not None and (self.playoff_teams < 2 or self.playoff_teams > 16):
            raise ValueError("Playoff teams must be 2-16")


@dataclass
class FantasyTeam:
    """Fantasy team model"""

    owner_name: str
    team_name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    platform_team_id: str | None = None
    wins: int = 0
    losses: int = 0
    ties: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate fantasy team data"""
        if not self.owner_name or len(self.owner_name) > 100:
            raise ValueError("Owner name must be 1-100 characters")
        if not self.team_name or len(self.team_name) > 100:
            raise ValueError("Team name must be 1-100 characters")
        if self.wins < 0 or self.losses < 0 or self.ties < 0:
            raise ValueError("Record values must be non-negative")
        if self.points_for < 0 or self.points_against < 0:
            raise ValueError("Points values must be non-negative")


@dataclass
class RosterPosition:
    """Roster position model"""

    position: Position
    count: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_bench: int = 0  # SQLite boolean as integer
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate roster position data"""
        if self.count < 0 or self.count > 10:
            raise ValueError("Position count must be 0-10")


@dataclass
class RosterEntry:
    """Roster entry model"""

    fantasy_team_id: str
    player_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    roster_position_id: str | None = None
    is_starting: int = 0  # SQLite boolean as integer
    acquired_date: str | None = None  # SQLite date as string
    acquisition_type: AcquisitionType | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class NFLGame:
    """NFL game model"""

    season_year: int
    week: int
    home_team_id: str
    away_team_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    game_date: str | None = None  # SQLite datetime as string
    home_score: int | None = None
    away_score: int | None = None
    game_status: GameStatus = GameStatus.SCHEDULED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate NFL game data"""
        if self.season_year < 2000 or self.season_year > 2030:
            raise ValueError("Season year must be 2000-2030")
        if self.week < 1 or self.week > 21:
            raise ValueError("Week must be 1-21")
        if self.home_score is not None and self.home_score < 0:
            raise ValueError("Home score must be non-negative")
        if self.away_score is not None and self.away_score < 0:
            raise ValueError("Away score must be non-negative")


@dataclass
class PlayerGameStats:
    """Player game statistics model"""

    player_id: str
    nfl_game_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    passing_yards: int = 0
    passing_touchdowns: int = 0
    passing_interceptions: int = 0
    rushing_yards: int = 0
    rushing_touchdowns: int = 0
    receiving_yards: int = 0
    receiving_touchdowns: int = 0
    receptions: int = 0
    targets: int = 0
    fumbles_lost: int = 0
    field_goals_made: int = 0
    field_goals_attempted: int = 0
    extra_points_made: int = 0
    extra_points_attempted: int = 0
    fantasy_points: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate player game stats"""
        if any(
            value < 0
            for value in [
                self.passing_yards,
                self.passing_touchdowns,
                self.passing_interceptions,
                self.rushing_yards,
                self.rushing_touchdowns,
                self.receiving_yards,
                self.receiving_touchdowns,
                self.receptions,
                self.targets,
                self.fumbles_lost,
                self.field_goals_made,
                self.field_goals_attempted,
                self.extra_points_made,
                self.extra_points_attempted,
            ]
        ):
            raise ValueError("All stat values must be non-negative")
        if self.fantasy_points < 0:
            raise ValueError("Fantasy points must be non-negative")


@dataclass
class TeamDefenseGameStats:
    """Team defense game statistics model"""

    nfl_team_id: str
    nfl_game_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sacks: int = 0
    interceptions: int = 0
    fumbles_recovered: int = 0
    safeties: int = 0
    touchdowns: int = 0
    points_allowed: int = 0
    yards_allowed: int = 0
    fantasy_points: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate team defense game stats"""
        if any(
            value < 0
            for value in [
                self.sacks,
                self.interceptions,
                self.fumbles_recovered,
                self.safeties,
                self.touchdowns,
                self.points_allowed,
                self.yards_allowed,
            ]
        ):
            raise ValueError("All stat values must be non-negative")
        if self.fantasy_points < 0:
            raise ValueError("Fantasy points must be non-negative")


@dataclass
class FantasyMatchup:
    """Fantasy matchup model"""

    week: int
    home_team_id: str
    away_team_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    home_score: float = 0.0
    away_score: float = 0.0
    winner_id: str | None = None
    is_playoff: int = 0  # SQLite boolean as integer
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate fantasy matchup data"""
        if self.week < 1 or self.week > 21:
            raise ValueError("Week must be 1-21")
        if self.home_score < 0 or self.away_score < 0:
            raise ValueError("Scores must be non-negative")


@dataclass
class FantasyTeamWeeklyScore:
    """Fantasy team weekly score model"""

    fantasy_team_id: str
    week: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_score: float = 0.0
    bench_score: float = 0.0
    optimal_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate fantasy team weekly score data"""
        if self.week < 1 or self.week > 21:
            raise ValueError("Week must be 1-21")
        if any(score < 0 for score in [self.total_score, self.bench_score, self.optimal_score]):
            raise ValueError("All scores must be non-negative")


@dataclass
class PlayerProjection:
    """Player projection model"""

    player_id: str
    week: int
    season_year: int
    source: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    projected_fantasy_points: float | None = None
    projected_passing_yards: int | None = None
    projected_passing_touchdowns: int | None = None
    projected_rushing_yards: int | None = None
    projected_rushing_touchdowns: int | None = None
    projected_receiving_yards: int | None = None
    projected_receiving_touchdowns: int | None = None
    projected_receptions: int | None = None
    confidence_rating: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate player projection data"""
        if self.week < 1 or self.week > 21:
            raise ValueError("Week must be 1-21")
        if self.season_year < 2000 or self.season_year > 2030:
            raise ValueError("Season year must be 2000-2030")
        if not self.source or len(self.source) > 50:
            raise ValueError("Source must be 1-50 characters")
        if self.confidence_rating is not None and (
            self.confidence_rating < 1 or self.confidence_rating > 10
        ):
            raise ValueError("Confidence rating must be 1-10")


@dataclass
class PlayerRanking:
    """Player ranking model"""

    player_id: str
    position: Position
    source: str
    rank: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    week: int | None = None
    season_year: int | None = None
    tier: int | None = None
    notes: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate player ranking data"""
        if self.week is not None and (self.week < 1 or self.week > 21):
            raise ValueError("Week must be 1-21")
        if self.season_year is not None and (self.season_year < 2000 or self.season_year > 2030):
            raise ValueError("Season year must be 2000-2030")
        if not self.source or len(self.source) > 50:
            raise ValueError("Source must be 1-50 characters")
        if self.rank < 1:
            raise ValueError("Rank must be positive")
        if self.tier is not None and self.tier < 1:
            raise ValueError("Tier must be positive")


@dataclass
class TradeProposal:
    """Trade proposal model"""

    proposing_team_id: str
    receiving_team_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TradeStatus = TradeStatus.PENDING
    proposed_date: str = field(default_factory=lambda: datetime.now().isoformat())
    response_date: str | None = None
    notes: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TradeItem:
    """Trade item model"""

    trade_proposal_id: str
    team_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str | None = None
    draft_round: int | None = None
    draft_pick_year: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate trade item data"""
        if self.player_id is None and (self.draft_round is None or self.draft_pick_year is None):
            raise ValueError("Must specify either player_id or draft pick details")
        if self.draft_round is not None and (self.draft_round < 1 or self.draft_round > 20):
            raise ValueError("Draft round must be 1-20")
        if self.draft_pick_year is not None and (
            self.draft_pick_year < 2000 or self.draft_pick_year > 2030
        ):
            raise ValueError("Draft pick year must be 2000-2030")


@dataclass
class TradeAnalysis:
    """Trade analysis model"""

    trade_proposal_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    team_a_value: float | None = None
    team_b_value: float | None = None
    team_a_roster_improvement: float | None = None
    team_b_roster_improvement: float | None = None
    analysis_notes: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate trade analysis data"""
        if self.team_a_roster_improvement is not None and (
            self.team_a_roster_improvement < -100 or self.team_a_roster_improvement > 100
        ):
            raise ValueError("Roster improvement must be -100 to 100")
        if self.team_b_roster_improvement is not None and (
            self.team_b_roster_improvement < -100 or self.team_b_roster_improvement > 100
        ):
            raise ValueError("Roster improvement must be -100 to 100")


@dataclass
class WaiverPriority:
    """Waiver priority model"""

    fantasy_team_id: str
    priority_order: int
    season_year: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate waiver priority data"""
        if self.priority_order < 1:
            raise ValueError("Priority order must be positive")
        if self.season_year < 2000 or self.season_year > 2030:
            raise ValueError("Season year must be 2000-2030")


@dataclass
class FreeAgentRecommendation:
    """Free agent recommendation model"""

    player_id: str
    week: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_reason: str | None = None
    priority_level: int | None = None
    projected_roster_impact: float | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate free agent recommendation data"""
        if self.week < 1 or self.week > 21:
            raise ValueError("Week must be 1-21")
        if self.priority_level is not None and (self.priority_level < 1 or self.priority_level > 5):
            raise ValueError("Priority level must be 1-5")
        if self.projected_roster_impact is not None and (
            self.projected_roster_impact < -100 or self.projected_roster_impact > 100
        ):
            raise ValueError("Projected roster impact must be -100 to 100")
