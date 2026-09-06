from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_title_returns_validation_error():
    response = client.post(
        "/issues",
        json={
            "body": "Missing title"
        },
    )

    assert response.status_code == 400

def test_empty_title_returns_validation_error():
    response = client.post(
        "/issues",
        json={
            "title": "",
            "body": "Empty title"
        },
    )

    assert response.status_code == 400


def test_invalid_state_returns_validation_error():
    response = client.patch(
        "/issues/1",
        json={
            "state": "invalid"
        },
    )

    assert response.status_code == 400


def test_invalid_list_state_returns_validation_error():
    response = client.get(
        "/issues",
        params={
            "state": "invalid"
        },
    )

    assert response.status_code == 400


def test_invalid_page_returns_validation_error():
    response = client.get(
        "/issues",
        params={
            "page": 0
        },
    )

    assert response.status_code == 400


def test_invalid_per_page_returns_validation_error():
    response = client.get(
        "/issues",
        params={
            "per_page": 101
        },
    )

    assert response.status_code == 400


def test_healthz():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }
