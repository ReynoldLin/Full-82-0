"""
Shared helpers used across pipeline scripts.
"""

import re

# Suffixes that basketball-reference strips out before building a slug.
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def _clean_name_part(name_part: str) -> str:
    """Lowercase and strip everything except a-z (drops apostrophes, periods,
    hyphens, spaces, accents-as-typed, etc.)."""
    return re.sub(r"[^a-z]", "", name_part.lower())


def _strip_suffix(last_name: str) -> str:
    """Remove a trailing suffix token like 'Jr.' / 'III' from a last name
    before slugging, e.g. 'Robinson III' -> 'Robinson'."""
    tokens = last_name.split()
    if len(tokens) > 1 and _clean_name_part(tokens[-1]) in _SUFFIXES:
        return " ".join(tokens[:-1])
    return last_name


def generate_slug(first_name: str, last_name: str, occurrence: int = 1) -> str:
    """Build a basketball-reference-style player slug.

    Formula: first 5 letters of last name + first 2 letters of first name +
    two-digit occurrence number. Punctuation and suffixes are stripped first.

    This is a *best guess* generated locally — it is not guaranteed to match
    basketball-reference's actual occurrence numbering for players who share
    a base slug (e.g. two different "Robinson, G..." players). The scraper
    verifies the name on the fetched page against the expected player and
    falls back to looking up the correct slug from basketball-reference's
    player index when it doesn't match.
    """
    last_clean = _clean_name_part(_strip_suffix(last_name))
    first_clean = _clean_name_part(first_name)

    base = last_clean[:5] + first_clean[:2]
    return f"{base}{occurrence:02d}"


def season_to_decade(season_start_year: int) -> int:
    """Map a season's start year to its decade bucket.

    Convention: a season is assigned to the decade containing its *second*
    year. e.g. the 2009-10 season (season_start_year=2009) ends in 2010,
    so it counts as the 2010s. The 1999-00 season (season_start_year=1999)
    ends in 2000, so it counts as the 2000s.
    """
    season_end_year = season_start_year + 1
    return (season_end_year // 10) * 10