"""Story 002: server-rendered pages."""


def send(api, token, hostname, packages):
    body = {
        "hostname": hostname,
        "collected_at": "2026-11-10T08:00:00Z",
        "os": {"distribution": "Ubuntu", "version": "22.04", "kernel": "5.15.0-118-generic"},
        "packages": [{"name": n, "version": v} for n, v in packages],
    }
    response = api.post(
        "/api/v1/inventory", json=body, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201


def test_index_lists_clients(api, make_client):
    _, token = make_client("client-a")
    make_client("client-b")
    send(api, token, "vm-01", [])

    page = api.get("/")

    assert page.status_code == 200
    assert "Client-A" in page.text and "Client-B" in page.text
    assert "2026-11-10 08:00" in page.text


def test_client_page_shows_only_its_hosts(api, make_client):
    _, token_a = make_client("client-a")
    _, token_b = make_client("client-b")
    send(api, token_a, "vm-a1", [("nginx", "1.18.0-6ubuntu14.4"), ("redis-server", "5:6.0.16")])
    send(api, token_b, "vm-b1", [])

    page = api.get("/clients/client-a")

    assert page.status_code == 200
    assert "vm-a1" in page.text and "Ubuntu 22.04" in page.text
    assert '<td class="num">2</td>' in page.text
    assert "vm-b1" not in page.text


def test_host_page_lists_and_filters_packages(api, make_client):
    _, token = make_client("client-a")
    send(api, token, "vm-01", [("nginx", "1.18.0-6ubuntu14.4"), ("redis-server", "5:6.0.16")])

    full = api.get("/clients/client-a/hosts/vm-01")
    filtered = api.get("/clients/client-a/hosts/vm-01", params={"q": "REDIS"})

    assert "nginx" in full.text and "redis-server" in full.text
    assert "redis-server" in filtered.text and "nginx" not in filtered.text


def test_unknown_or_foreign_resources_are_404(api, make_client):
    make_client("client-a")
    _, token_b = make_client("client-b")
    send(api, token_b, "vm-b1", [])

    assert api.get("/clients/unknown").status_code == 404
    assert api.get("/clients/client-a/hosts/missing").status_code == 404
    # client-b's host is not reachable through client-a's URL
    assert api.get("/clients/client-a/hosts/vm-b1").status_code == 404


def test_collected_values_are_html_escaped(api, make_client):
    _, token = make_client("client-a")
    send(api, token, "vm-01", [("<script>alert(1)</script>", "1.0")])

    page = api.get("/clients/client-a/hosts/vm-01")

    assert "<script>alert(1)</script>" not in page.text
    assert "&lt;script&gt;" in page.text
