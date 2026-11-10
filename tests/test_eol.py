"""Story 003: OS end-of-life (no network: endoflife.date is faked)."""

from datetime import date

import pytest
from sqlalchemy import func, select

from kairos.eol import cycle_key, os_status, sync_release_cycles
from kairos.models import ReleaseCycle

UBUNTU = [
    {"cycle": "24.04", "codename": "Noble Numbat", "lts": True, "releaseDate": "2024-04-25",
     "eol": "2029-05-31", "extendedSupport": "2036-04-25", "latest": "24.04.3"},
    {"cycle": "22.04", "codename": "Jammy Jellyfish", "lts": True, "releaseDate": "2022-04-21",
     "eol": "2027-06-01", "extendedSupport": "2034-04-21", "latest": "22.04.5"},
    {"cycle": "23.10", "codename": "Mantic Minotaur", "lts": False, "releaseDate": "2023-10-12",
     "eol": "2024-07-11", "extendedSupport": False, "latest": "23.10"},
]  # fmt: skip


def fake_fetch(_product):
    return UBUNTU


def cycle(eol, extended=None):
    return ReleaseCycle(product="ubuntu", cycle="x", eol=eol, extended_support=extended)


def test_sync_is_idempotent(session_factory):
    with session_factory() as session:
        assert sync_release_cycles(session, fake_fetch) == 3
        sync_release_cycles(session, fake_fetch)
        total = session.scalar(select(func.count()).select_from(ReleaseCycle))
        jammy = session.scalar(select(ReleaseCycle).where(ReleaseCycle.cycle == "22.04"))
    assert total == 3
    assert (jammy.lts, jammy.eol, jammy.extended_support) == (
        True,
        date(2027, 6, 1),
        date(2034, 4, 21),
    )


@pytest.mark.parametrize(
    ("today", "level", "label"),
    [
        (date(2026, 11, 10), "ok", "Supporté"),
        (date(2027, 3, 1), "warning", "Fin de support proche"),
        (date(2028, 1, 1), "critical", "Support standard terminé (Ubuntu Pro)"),
        (date(2035, 1, 1), "critical", "Fin de vie"),
    ],
)
def test_os_status(today, level, label):
    status = os_status(cycle(date(2027, 6, 1), date(2034, 4, 21)), today)
    assert (status.level, status.label) == (level, label)


def test_unknown_cycle_and_non_lts_without_extended_support():
    assert os_status(None, date(2026, 11, 10)).level == "unknown"
    assert os_status(cycle(None), date(2026, 11, 10)).label == "Supporté (fin non annoncée)"
    status = os_status(cycle(date(2024, 7, 11)), date(2026, 11, 10))
    assert (status.level, status.label) == ("critical", "Fin de vie")


def test_cycle_key():
    assert cycle_key("Ubuntu", "22.04") == ("ubuntu", "22.04")
    assert cycle_key("Ubuntu", "22.04.5") == ("ubuntu", "22.04")
    assert cycle_key("Debian", "12") is None
    assert cycle_key(None, "22.04") is None


def test_client_and_host_pages_show_os_status(api, make_client, session_factory):
    _, token = make_client("client-a")
    with session_factory() as session:
        sync_release_cycles(session, fake_fetch)
    body = {
        "hostname": "vm-01",
        "collected_at": "2026-11-10T08:00:00Z",
        "os": {"distribution": "Ubuntu", "version": "23.10", "kernel": "6.5.0-44-generic"},
        "packages": [],
    }
    api.post("/api/v1/inventory", json=body, headers={"Authorization": f"Bearer {token}"})

    client_page = api.get("/clients/client-a").text
    host_page = api.get("/clients/client-a/hosts/vm-01").text

    assert 'class="badge critical">Fin de vie' in client_page
    assert "11/07/2024" in client_page
    assert 'class="badge critical">Fin de vie' in host_page
