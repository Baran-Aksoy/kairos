"""Collect tokens: random secrets shown once, stored only as SHA-256.

SHA-256 without salt is sufficient here because tokens are 256-bit random values,
not user-chosen passwords.
"""

import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from kairos.models import Client, CollectToken


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_collect_token(session: Session, client: Client) -> str:
    """Create a token for ``client`` and return it in clear text (the only time it exists)."""
    token = secrets.token_urlsafe(32)
    session.add(CollectToken(client_id=client.id, token_hash=hash_token(token)))
    return token


def client_id_for_token(session: Session, token: str) -> int | None:
    return session.scalar(
        select(CollectToken.client_id).where(CollectToken.token_hash == hash_token(token))
    )
