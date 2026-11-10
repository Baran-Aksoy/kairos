"""Operations commands: ``python -m kairos <command>``."""

import argparse
import re
import sys
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from kairos.models import Client, Host
from kairos.tokens import create_collect_token

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def create_client(session: Session, slug: str, name: str) -> int:
    if not SLUG_RE.match(slug):
        print("Invalid slug: lowercase letters, digits and dashes only.", file=sys.stderr)
        return 1
    if session.scalar(select(Client).where(Client.slug == slug)):
        print(f"Client '{slug}' already exists.", file=sys.stderr)
        return 1
    client = Client(slug=slug, name=name)
    session.add(client)
    session.flush()
    token = create_collect_token(session, client)
    session.commit()
    print(f"Client '{slug}' created.")
    print("Collect token (shown only once, store it in an AWX credential):")
    print(token)
    return 0


def list_hosts(session: Session, slug: str) -> int:
    client = session.scalar(select(Client).where(Client.slug == slug))
    if client is None:
        print(f"Unknown client '{slug}'.", file=sys.stderr)
        return 1
    hosts = session.scalars(
        select(Host).where(Host.client_id == client.id).order_by(Host.hostname)
    ).all()
    if not hosts:
        print(f"No host collected yet for '{slug}'.")
    for host in hosts:
        print(f"{host.hostname}\tlast collected {host.last_seen:%Y-%m-%d %H:%M:%S}")
    return 0


def main(
    argv: list[str] | None = None, session_factory: Callable[[], Session] | None = None
) -> int:
    parser = argparse.ArgumentParser(prog="python -m kairos")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create-client", help="create a client and its collect token")
    create.add_argument("slug", help="short identifier, e.g. client-a")
    create.add_argument("name", help="display name")

    hosts = commands.add_parser("hosts", help="list a client's hosts and last collection date")
    hosts.add_argument("slug")

    commands.add_parser("sync-eol", help="refresh OS end-of-life data from endoflife.date")

    args = parser.parse_args(argv)

    if session_factory is None:
        from sqlalchemy.orm import sessionmaker

        from kairos.db import get_engine

        session_factory = sessionmaker(bind=get_engine())

    with session_factory() as session:
        if args.command == "create-client":
            return create_client(session, args.slug, args.name)
        if args.command == "sync-eol":
            from kairos.eol import sync_release_cycles

            print(f"{sync_release_cycles(session)} release cycles synced.")
            return 0
        return list_hosts(session, args.slug)
