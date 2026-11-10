"""OS end-of-life: sync from endoflife.date and status computation (story 003)."""

import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from kairos.models import ReleaseCycle

API_URL = "https://endoflife.date/api/{product}.json"
SUPPORTED_PRODUCTS = ("ubuntu",)
WARNING_WINDOW = timedelta(days=180)

Fetcher = Callable[[str], list[dict]]


def fetch_endoflife(product: str) -> list[dict]:
    request = urllib.request.Request(  # noqa: S310 - fixed https URL
        API_URL.format(product=product), headers={"User-Agent": "kairos"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return json.load(response)


def _as_date(value: object) -> date | None:
    """endoflife.date uses either an ISO date or a boolean for date fields."""
    return date.fromisoformat(value) if isinstance(value, str) else None


def sync_release_cycles(session: Session, fetch: Fetcher = fetch_endoflife) -> int:
    """Upsert the release cycles of every supported product. Returns the number of cycles."""
    now = datetime.now(UTC)
    count = 0
    for product in SUPPORTED_PRODUCTS:
        existing = {
            c.cycle: c
            for c in session.scalars(select(ReleaseCycle).where(ReleaseCycle.product == product))
        }
        for item in fetch(product):
            if not item.get("cycle"):
                continue  # unexpected format: skip rather than fail the whole sync
            cycle = existing.get(str(item["cycle"])) or ReleaseCycle(
                product=product, cycle=str(item["cycle"])
            )
            cycle.codename = item.get("codename")
            cycle.lts = bool(item.get("lts"))
            cycle.release_date = _as_date(item.get("releaseDate"))
            cycle.eol = _as_date(item.get("eol"))
            cycle.extended_support = _as_date(item.get("extendedSupport"))
            cycle.latest = item.get("latest")
            cycle.fetched_at = now
            session.add(cycle)
            count += 1
    session.commit()
    return count


@dataclass(frozen=True)
class OsStatus:
    level: str  # ok | warning | critical | unknown
    label: str
    until: date | None = None


def os_status(cycle: ReleaseCycle | None, today: date) -> OsStatus:
    if cycle is None:
        return OsStatus("unknown", "Inconnu")
    if cycle.eol is None:  # endoflife.date sends "eol": false when no end date is announced
        return OsStatus("ok", "Supporté (fin non annoncée)")
    if today <= cycle.eol:
        if cycle.eol - today <= WARNING_WINDOW:
            return OsStatus("warning", "Fin de support proche", cycle.eol)
        return OsStatus("ok", "Supporté", cycle.eol)
    if cycle.extended_support and today <= cycle.extended_support:
        return OsStatus("critical", "Support standard terminé (Ubuntu Pro)", cycle.extended_support)
    return OsStatus("critical", "Fin de vie", cycle.extended_support or cycle.eol)


def cycle_key(distribution: str | None, version: str | None) -> tuple[str, str] | None:
    """Map collected OS facts to an endoflife.date (product, cycle)."""
    if not distribution or not version:
        return None
    product = distribution.lower()
    if product not in SUPPORTED_PRODUCTS:
        return None
    return product, ".".join(version.split(".")[:2])  # "22.04.5" -> "22.04"


def release_cycles_by_key(session: Session) -> dict[tuple[str, str], ReleaseCycle]:
    return {(c.product, c.cycle): c for c in session.scalars(select(ReleaseCycle))}


def today_utc() -> date:
    return datetime.now(UTC).date()
