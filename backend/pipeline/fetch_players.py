"""
Pipeline step 1: populate `teams` and `players` from nba_api's static data.

Run manually:
    python -m pipeline.fetch_players

What this does:
    1. Pulls the 30 current NBA franchises from nba_api and upserts them
       into `teams`. (Historical/relocated franchises, e.g. the Seattle
       SuperSonics, are NOT included here — nba_api's static team list only
       has current franchises. Those get added later by the scraper, as it
       encounters team abbreviations on basketball-reference that don't
       exist yet.)
    2. Pulls every player in NBA history from nba_api and upserts them into
       `players`, computing a best-guess basketball-reference slug for each.

This script only touches `teams` and `players`. It does not fetch any
stats — that happens in scrape_player_stats.py, which also verifies (and
corrects, if needed) the slugs generated here.
"""

import logging
from collections import defaultdict

from nba_api.stats.static import players as nba_players
from nba_api.stats.static import teams as nba_teams
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Player, Team
from pipeline.utils import generate_slug

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def upsert_teams(db: Session) -> None:
    teams_data = nba_teams.get_teams()
    logger.info("Fetched %d teams from nba_api", len(teams_data))

    for t in teams_data:
        existing = db.get(Team, t["id"])
        if existing:
            existing.abbreviation = t["abbreviation"]
            existing.full_name = t["full_name"]
        else:
            db.add(
                Team(
                    team_id=t["id"],
                    abbreviation=t["abbreviation"],
                    full_name=t["full_name"],
                )
            )
    db.commit()
    logger.info("Teams upserted.")


def upsert_players(db: Session) -> None:
    players_data = nba_players.get_players()
    logger.info("Fetched %d players from nba_api", len(players_data))

    # Sort by nba_api id ascending as a (rough) proxy for chronological order,
    # so that when two players share a base slug, the earlier-id player tends
    # to land on 01. This is only a best guess -- the scraper verifies/fixes
    # it against the actual basketball-reference page.
    players_data = sorted(players_data, key=lambda p: p["id"])

    # Tracks how many players we've already assigned to each base slug
    # (last5 + first2) so we can increment the occurrence number.
    slug_occurrence_count: dict[str, int] = defaultdict(int)

    inserted, updated = 0, 0

    for p in players_data:
        base_slug = generate_slug(p["first_name"], p["last_name"], occurrence=1)[:-2]
        slug_occurrence_count[base_slug] += 1
        occurrence = slug_occurrence_count[base_slug]
        slug = generate_slug(p["first_name"], p["last_name"], occurrence=occurrence)

        existing = db.get(Player, p["id"])
        if existing:
            existing.full_name = p["full_name"]
            existing.slug = slug
            existing.is_active = p["is_active"]
            updated += 1
        else:
            db.add(
                Player(
                    player_id=p["id"],
                    full_name=p["full_name"],
                    slug=slug,
                    nba_api_id=p["id"],
                    is_active=p["is_active"],
                )
            )
            inserted += 1

    db.commit()
    logger.info("Players upserted. inserted=%d updated=%d", inserted, updated)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        upsert_teams(db)
        upsert_players(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()