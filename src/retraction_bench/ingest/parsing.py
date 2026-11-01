"""Pure parsing helpers for the raw Retraction Watch CSV.

Kept separate from I/O (download, DuckDB, report writing) so they can be
unit-tested directly against edge cases without touching the network or a
database. Every function here is strict: an unparseable or ambiguous input
returns a clear "unknown" signal rather than guessing.
"""

import re
from datetime import date, datetime

# Retraction Watch's own documented sentinels for "no value" (see the source
# repo's README): dates/DOIs may be blank; identifiers may also be the
# literal strings "unavailable" / "Unavailable", and PubMed IDs may be "0".
_MISSING_SENTINELS = {"", "unavailable", "0"}

# Retraction Watch dates are consistently "M/D/YYYY H:MM" in the source CSV.
_RW_DATE_FORMAT = "%m/%d/%Y %H:%M"

# Permissive but real DOI syntax: 10.<4-9 digit registrant>/<suffix>.
_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


def is_missing_value(raw: str | None) -> bool:
    """True if `raw` is one of Retraction Watch's documented "no value" sentinels."""
    if raw is None:
        return True
    return raw.strip().casefold() in _MISSING_SENTINELS


def is_resolvable_doi(raw: str | None) -> bool:
    """True if `raw` is present and matches DOI syntax (10.<registrant>/<suffix>)."""
    if is_missing_value(raw):
        return False
    return bool(_DOI_PATTERN.match(raw.strip()))


def parse_rw_date(raw: str | None) -> date | None:
    """Strictly parse a Retraction Watch "M/D/YYYY H:MM" date string.

    Returns None for any missing, malformed, or ambiguous value -- callers
    are responsible for counting and recording these, never silently
    coercing them (see docs/DECISIONS.md).
    """
    if is_missing_value(raw):
        return None
    try:
        return datetime.strptime(raw.strip(), _RW_DATE_FORMAT).date()
    except ValueError:
        return None


def split_multivalue(raw: str | None) -> list[str]:
    """Split a semicolon-delimited Retraction Watch field into trimmed, non-empty values."""
    if raw is None:
        return []
    return [part.strip() for part in raw.split(";") if part.strip()]
