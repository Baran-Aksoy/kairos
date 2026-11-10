"""Story 001, end to end: the real playbook, run locally, fills the database through the API."""

import os
import shutil
import socket
import subprocess
import threading
import time

import pytest
import uvicorn
from conftest import ROOT
from sqlalchemy import func, select

from kairos.models import Host, Installation, Snapshot

ANSIBLE_PLAYBOOK = shutil.which("ansible-playbook")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def live_api(app_with_db):
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app_with_db, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


@pytest.mark.skipif(ANSIBLE_PLAYBOOK is None, reason="ansible-playbook not installed")
def test_playbook_sends_inventory(live_api, make_client, session_factory):
    client_id, token = make_client("client-a")
    env = os.environ | {"KAIROS_URL": live_api, "KAIROS_TOKEN": token, "ANSIBLE_NOCOLOR": "1"}

    run = subprocess.run(  # noqa: S603 - fixed arguments, no user input
        [ANSIBLE_PLAYBOOK, "-i", "vm-01,", "-c", "local", "ansible/collect.yml"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert run.returncode == 0, run.stdout[-3000:] + run.stderr[-2000:]
    assert token not in run.stdout + run.stderr
    with session_factory() as session:
        host = session.scalar(select(Host))
        snapshot = session.scalar(select(Snapshot))
        packages = session.scalar(select(func.count()).select_from(Installation))
    assert (host.client_id, host.hostname) == (client_id, "vm-01")
    assert snapshot.os_distribution == "Ubuntu"
    assert snapshot.os_version and snapshot.kernel_running
    assert packages > 0
