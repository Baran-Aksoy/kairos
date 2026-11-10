from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from kairos.db import get_session
from kairos.models import Host, Installation, Snapshot
from kairos.schemas import InventoryIn, InventoryOut
from kairos.tokens import client_id_for_token

router = APIRouter(prefix="/api/v1")
bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


def collecting_client_id(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> int:
    """Resolve the client from the collect token. The token is never logged nor returned."""
    client_id = client_id_for_token(session, credentials.credentials) if credentials else None
    if client_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing collect token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return client_id


@router.post("/inventory", status_code=status.HTTP_201_CREATED)
def receive_inventory(
    inventory: InventoryIn,
    session: SessionDep,
    client_id: Annotated[int, Depends(collecting_client_id)],
) -> InventoryOut:
    """Store one host inventory in a single transaction: all or nothing.

    Nothing is committed before the final commit; on any error the session is closed
    by get_session and the transaction is rolled back.
    """
    host = session.scalar(
        select(Host).where(Host.client_id == client_id, Host.hostname == inventory.hostname)
    )
    if host is None:
        host = Host(client_id=client_id, hostname=inventory.hostname)
        session.add(host)
    host.machine_id = inventory.machine_id or None  # Ansible sends "" when unknown
    host.last_seen = inventory.collected_at

    snapshot = Snapshot(
        client_id=client_id,
        host=host,
        collected_at=inventory.collected_at,
        os_distribution=inventory.os.distribution,
        os_version=inventory.os.version,
        kernel_running=inventory.os.kernel,
        # Packages live in installations; raw keeps the rest of what was received.
        raw=inventory.model_dump(mode="json", exclude={"packages"}),
    )
    session.add(snapshot)
    session.flush()

    # package_facts may list the same package once per architecture.
    unique_packages = sorted({(p.name, p.version) for p in inventory.packages})
    if unique_packages:
        session.execute(
            insert(Installation),
            [
                {
                    "client_id": client_id,
                    "snapshot_id": snapshot.id,
                    "name": name,
                    "version": version,
                    # Story 001 covers apt only; other sources come with their detectors.
                    "source": "apt",
                    "detection_method": "package",
                }
                for name, version in unique_packages
            ],
        )
    session.commit()

    return InventoryOut(
        hostname=host.hostname, snapshot_id=snapshot.id, packages=len(unique_packages)
    )
