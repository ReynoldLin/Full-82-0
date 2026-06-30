"""
SQLAlchemy ORM models — this defines the actual SQLite table structure.

Schema recap:
    teams
    players
    player_season_stats        (raw, scraped from basketball-reference)
    player_team_decade_stats   (aggregated from player_season_stats)
    lineups
    lineup_picks
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(primary_key=True)
    abbreviation: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))

    season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), index=True)
    slug: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nba_api_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    positions: Mapped[str] = mapped_column(String(50), default="")  # distinct positions across career, e.g. "PG, SG"

    season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(back_populates="player")


class PlayerSeasonStats(Base):
    """One row per player, per team, per season. Raw scrape from basketball-reference's
    Totals table. TOT (combined) rows are skipped at scrape time."""

    __tablename__ = "player_season_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "team_id", "season_start_year", name="uq_player_team_season"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"), index=True)

    season_start_year: Mapped[int] = mapped_column(Integer)  # e.g. 2009 for "2009-10"
    decade: Mapped[int] = mapped_column(Integer, index=True)  # e.g. 2010
    position: Mapped[str] = mapped_column(String(10), default="")  # e.g. "PG", "SG-SF"
    awards: Mapped[str] = mapped_column(String(100), default="")  # e.g. "MVP-1,AS,NBA1"

    games_played: Mapped[int] = mapped_column(Integer, default=0)
    games_started: Mapped[int] = mapped_column(Integer, default=0)
    minutes_played: Mapped[int] = mapped_column(Integer, default=0)

    fg: Mapped[int] = mapped_column(Integer, default=0)
    fga: Mapped[int] = mapped_column(Integer, default=0)
    fg3: Mapped[int] = mapped_column(Integer, default=0)
    fg3a: Mapped[int] = mapped_column(Integer, default=0)
    ft: Mapped[int] = mapped_column(Integer, default=0)
    fta: Mapped[int] = mapped_column(Integer, default=0)

    trb: Mapped[int] = mapped_column(Integer, default=0)
    ast: Mapped[int] = mapped_column(Integer, default=0)
    stl: Mapped[int] = mapped_column(Integer, default=0)
    blk: Mapped[int] = mapped_column(Integer, default=0)
    tov: Mapped[int] = mapped_column(Integer, default=0)
    pts: Mapped[int] = mapped_column(Integer, default=0)

    player: Mapped["Player"] = relationship(back_populates="season_stats")
    team: Mapped["Team"] = relationship(back_populates="season_stats")


class PlayerTeamDecadeStats(Base):
    """Aggregated from PlayerSeasonStats, grouped by (player, team, decade).
    This is the table the live game actually queries when a slot is filled."""

    __tablename__ = "player_team_decade_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "team_id", "decade", name="uq_player_team_decade"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"), index=True)
    decade: Mapped[int] = mapped_column(Integer, index=True)
    positions: Mapped[str] = mapped_column(String(50), default="")
    awards: Mapped[str] = mapped_column(String(200), default="")

    games_played: Mapped[int] = mapped_column(Integer, default=0)

    pts_per_game: Mapped[float] = mapped_column(Float, default=0.0)
    reb_per_game: Mapped[float] = mapped_column(Float, default=0.0)
    ast_per_game: Mapped[float] = mapped_column(Float, default=0.0)
    stl_per_game: Mapped[float] = mapped_column(Float, default=0.0)
    blk_per_game: Mapped[float] = mapped_column(Float, default=0.0)
    tov_per_game: Mapped[float] = mapped_column(Float, default=0.0)

    fg_pct: Mapped[float] = mapped_column(Float, default=0.0)
    fg3_pct: Mapped[float] = mapped_column(Float, default=0.0)
    ft_pct: Mapped[float] = mapped_column(Float, default=0.0)


class Lineup(Base):
    __tablename__ = "lineups"

    lineup_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    picks: Mapped[list["LineupPick"]] = relationship(back_populates="lineup")


class LineupPick(Base):
    __tablename__ = "lineup_picks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lineup_id: Mapped[int] = mapped_column(ForeignKey("lineups.lineup_id"), index=True)
    slot_number: Mapped[int] = mapped_column(Integer)

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"))
    decade: Mapped[int] = mapped_column(Integer)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"))

    lineup: Mapped["Lineup"] = relationship(back_populates="picks")