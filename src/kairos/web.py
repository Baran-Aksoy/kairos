"""Server-rendered pages (story 002). Every query is scoped to one client."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kairos.db import get_session
from kairos.models import Client, Host, Installation, Snapshot

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
router = APIRouter(include_in_schema=False, default_response_class=HTMLResponse)
SessionDep = Annotated[Session, Depends(get_session)]


def _client_or_404(session: Session, slug: str) -> Client:
    client = session.scalar(select(Client).where(Client.slug == slug))
    if client is None:
        raise HTTPException(status_code=404, detail="Unknown client")
    return client


@router.get("/")
def index(request: Request, session: SessionDep):
    clients = session.execute(
        select(
            Client.slug,
            Client.name,
            func.count(Host.id).label("hosts"),
            func.max(Host.last_seen).label("last_seen"),
        )
        .outerjoin(Host, Host.client_id == Client.id)
        .group_by(Client.id)
        .order_by(Client.name)
    ).all()
    return templates.TemplateResponse(request, "index.html", {"clients": clients})


@router.get("/clients/{slug}")
def client_page(request: Request, slug: str, session: SessionDep):
    client = _client_or_404(session, slug)
    latest = (
        select(Snapshot.host_id, func.max(Snapshot.id).label("snapshot_id"))
        .where(Snapshot.client_id == client.id)
        .group_by(Snapshot.host_id)
        .subquery()
    )
    package_count = (
        select(func.count(Installation.id))
        .where(Installation.snapshot_id == Snapshot.id, Installation.client_id == client.id)
        .scalar_subquery()
    )
    hosts = session.execute(
        select(
            Host.hostname,
            Host.last_seen,
            Snapshot.os_distribution,
            Snapshot.os_version,
            Snapshot.kernel_running,
            package_count.label("packages"),
        )
        .join(latest, latest.c.host_id == Host.id)
        .join(Snapshot, Snapshot.id == latest.c.snapshot_id)
        .where(Host.client_id == client.id)
        .order_by(Host.hostname)
    ).all()
    return templates.TemplateResponse(request, "client.html", {"client": client, "hosts": hosts})


@router.get("/clients/{slug}/hosts/{hostname}")
def host_page(request: Request, slug: str, hostname: str, session: SessionDep, q: str = ""):
    client = _client_or_404(session, slug)
    host = session.scalar(
        select(Host).where(Host.client_id == client.id, Host.hostname == hostname)
    )
    snapshot = host and session.scalar(
        select(Snapshot)
        .where(Snapshot.client_id == client.id, Snapshot.host_id == host.id)
        .order_by(Snapshot.id.desc())
        .limit(1)
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Unknown host")

    packages = select(Installation).where(
        Installation.client_id == client.id, Installation.snapshot_id == snapshot.id
    )
    total = session.scalar(select(func.count()).select_from(packages.subquery()))
    if q.strip():
        packages = packages.where(Installation.name.icontains(q.strip(), autoescape=True))
    return templates.TemplateResponse(
        request,
        "host.html",
        {
            "client": client,
            "host": host,
            "snapshot": snapshot,
            "packages": session.scalars(packages.order_by(Installation.name)).all(),
            "total": total,
            "q": q,
        },
    )
