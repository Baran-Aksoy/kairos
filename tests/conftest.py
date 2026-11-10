import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from kairos.db import get_session
from kairos.main import app
from kairos.models import Base, Client
from kairos.tokens import create_collect_token

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def session_factory(tmp_path):
    """Throwaway SQLite database (file-based so the API can be served from a thread)."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'kairos.db'}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def app_with_db(session_factory):
    def _session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def api(app_with_db):
    return TestClient(app_with_db)


@pytest.fixture
def make_client(session_factory):
    """Create a client and return (client_id, clear-text collect token)."""

    def _make(slug: str) -> tuple[int, str]:
        with session_factory() as session:
            client = Client(slug=slug, name=slug.title())
            session.add(client)
            session.flush()
            token = create_collect_token(session, client)
            session.commit()
            return client.id, token

    return _make


def _load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def ansible_checker():
    return _load_script("check_ansible_readonly")


@pytest.fixture(scope="session")
def story_checker():
    return _load_script("check_story")
