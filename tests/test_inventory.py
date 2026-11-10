"""Story 001: receiving an inventory through POST /api/v1/inventory."""

import logging

from sqlalchemy import func, select

from kairos.models import CollectToken, Host, Installation, Snapshot
from kairos.tokens import hash_token

URL = "/api/v1/inventory"


def payload(hostname="vm-01", collected_at="2026-11-10T08:00:00Z", **overrides):
    body = {
        "hostname": hostname,
        "machine_id": "0123456789abcdef0123456789abcdef",
        "collected_at": collected_at,
        "os": {"distribution": "Ubuntu", "version": "22.04", "kernel": "5.15.0-118-generic"},
        "packages": [
            {"name": "openssh-server", "version": "1:8.9p1-3ubuntu0.10", "arch": "amd64"},
            {"name": "nginx", "version": "1.18.0-6ubuntu14.4", "source": "apt"},
            # same package for two architectures: stored once
            {"name": "libc6", "version": "2.35-0ubuntu3.8", "arch": "amd64"},
            {"name": "libc6", "version": "2.35-0ubuntu3.8", "arch": "i386"},
        ],
    }
    body.update(overrides)
    return body


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def count(session_factory, model, *where):
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(model).where(*where))


def test_inventory_is_stored(api, make_client, session_factory):
    client_id, token = make_client("client-a")

    response = api.post(URL, json=payload(), headers=auth(token))

    assert response.status_code == 201
    assert response.json() == {
        "hostname": "vm-01",
        "snapshot_id": response.json()["snapshot_id"],
        "packages": 3,
    }
    with session_factory() as session:
        host = session.scalar(select(Host))
        snapshot = session.scalar(select(Snapshot))
        installations = session.scalars(select(Installation)).all()
    assert (host.client_id, host.hostname) == (client_id, "vm-01")
    assert (snapshot.os_distribution, snapshot.os_version, snapshot.kernel_running) == (
        "Ubuntu",
        "22.04",
        "5.15.0-118-generic",
    )
    assert snapshot.collected_at is not None
    assert {(i.name, i.version) for i in installations} == {
        ("openssh-server", "1:8.9p1-3ubuntu0.10"),
        ("nginx", "1.18.0-6ubuntu14.4"),
        ("libc6", "2.35-0ubuntu3.8"),
    }
    assert {(i.source, i.detection_method, i.client_id) for i in installations} == {
        ("apt", "package", client_id)
    }


def test_missing_or_unknown_token_is_rejected(api, make_client, session_factory):
    make_client("client-a")

    no_token = api.post(URL, json=payload())
    bad_token = api.post(URL, json=payload(), headers=auth("not-a-real-token"))

    assert no_token.status_code == 401
    assert bad_token.status_code == 401
    assert count(session_factory, Host) == 0
    assert count(session_factory, Snapshot) == 0


def test_body_cannot_name_a_client(api, make_client, session_factory):
    _, token_a = make_client("client-a")
    make_client("client-b")

    response = api.post(URL, json=payload(client="client-b"), headers=auth(token_a))

    assert response.status_code == 422
    assert count(session_factory, Host) == 0


def test_same_hostname_never_mixes_clients(api, make_client, session_factory):
    client_a, token_a = make_client("client-a")
    client_b, token_b = make_client("client-b")

    api.post(URL, json=payload(), headers=auth(token_a))
    api.post(URL, json=payload(packages=[]), headers=auth(token_b))

    assert count(session_factory, Host, Host.client_id == client_a) == 1
    assert count(session_factory, Host, Host.client_id == client_b) == 1
    assert count(session_factory, Installation, Installation.client_id == client_a) == 3
    assert count(session_factory, Installation, Installation.client_id == client_b) == 0


def test_token_is_never_stored_returned_or_logged(api, make_client, session_factory, caplog):
    _, token = make_client("client-a")

    with caplog.at_level(logging.DEBUG):
        response = api.post(URL, json=payload(), headers=auth(token))

    with session_factory() as session:
        stored = session.scalars(select(CollectToken.token_hash)).all()
    assert stored == [hash_token(token)]
    assert token not in response.text
    assert token not in caplog.text


def test_resending_updates_host_and_adds_snapshot(api, make_client, session_factory):
    _, token = make_client("client-a")

    api.post(URL, json=payload(collected_at="2026-11-10T08:00:00Z"), headers=auth(token))
    api.post(URL, json=payload(collected_at="2026-11-11T08:00:00Z"), headers=auth(token))

    assert count(session_factory, Host) == 1
    assert count(session_factory, Snapshot) == 2
    with session_factory() as session:
        last_seen = session.scalar(select(Host.last_seen))
    assert last_seen.strftime("%Y-%m-%d") == "2026-11-11"


def test_invalid_payload_writes_nothing(api, make_client, session_factory):
    _, token = make_client("client-a")
    missing_os = payload()
    del missing_os["os"]
    empty_version = payload(packages=[{"name": "nginx", "version": ""}])

    assert api.post(URL, json=missing_os, headers=auth(token)).status_code == 422
    assert api.post(URL, json=empty_version, headers=auth(token)).status_code == 422
    assert count(session_factory, Host) == 0
    assert count(session_factory, Snapshot) == 0
    assert count(session_factory, Installation) == 0
