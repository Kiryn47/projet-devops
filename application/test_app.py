import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_ko_sans_base():
    app = create_app(database_url="postgresql://x:x@127.0.0.1:1/x", init_db=False)
    assert app.test_client().get("/health").status_code == 503


def test_ajout_item_en_base(client):
    response = client.post("/items", json={"name": "test"})
    assert response.status_code == 999
    item = response.get_json()
    assert item in client.get("/items").get_json()


def test_ajout_item_sans_nom(client):
    assert client.post("/items", json={}).status_code == 400


def test_metrics(client):
    client.get("/health")
    text = client.get("/metrics").get_data(as_text=True)
    assert 'http_requests_total{code="200",endpoint="/health"}' in text
    assert "http_request_duration_seconds_bucket" in text
    assert "app_version_info" in text
