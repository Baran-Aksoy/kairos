"""Story 001: operations commands (python -m kairos ...)."""

from sqlalchemy import select

from kairos.cli import main
from kairos.models import Client, CollectToken
from kairos.tokens import hash_token

URL = "/api/v1/inventory"


def test_create_client_prints_token_once_and_stores_its_hash(session_factory, capsys):
    assert main(["create-client", "client-a", "Client A"], session_factory) == 0

    token = capsys.readouterr().out.strip().splitlines()[-1]
    with session_factory() as session:
        assert session.scalar(select(Client.name).where(Client.slug == "client-a")) == "Client A"
        assert session.scalars(select(CollectToken.token_hash)).all() == [hash_token(token)]


def test_create_client_rejects_duplicates_and_bad_slugs(session_factory, capsys):
    main(["create-client", "client-a", "Client A"], session_factory)

    assert main(["create-client", "client-a", "Again"], session_factory) == 1
    assert main(["create-client", "Client A!", "Bad"], session_factory) == 1


def test_hosts_lists_hosts_with_last_collection(api, make_client, session_factory, capsys):
    _, token = make_client("client-a")
    make_client("client-b")
    body = {
        "hostname": "vm-01",
        "collected_at": "2026-11-10T08:00:00Z",
        "os": {"distribution": "Ubuntu", "version": "24.04", "kernel": "6.8.0-48-generic"},
        "packages": [],
    }
    api.post(URL, json=body, headers={"Authorization": f"Bearer {token}"})

    assert main(["hosts", "client-a"], session_factory) == 0
    assert "vm-01\tlast collected 2026-11-10 08:00:00" in capsys.readouterr().out

    assert main(["hosts", "client-b"], session_factory) == 0
    assert "vm-01" not in capsys.readouterr().out

    assert main(["hosts", "unknown"], session_factory) == 1


def test_collect_token_cannot_read(api, make_client):
    _, token = make_client("client-a")

    response = api.get(URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 405
