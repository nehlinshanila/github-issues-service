import hashlib
import hmac
import json
import os

from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv(".env")

from app.main import app

client = TestClient(app)


def make_signature(body: bytes) -> str:
    secret = os.getenv("WEBHOOK_SECRET", "").encode()

    digest = hmac.new(
        secret,
        body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_valid_webhook_signature():
    payload = {
        "action": "opened",
        "issue": {
            "number": 1
        },
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "unit-test-valid-001",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 204


def test_invalid_webhook_signature():
    payload = {
        "action": "opened",
        "issue": {
            "number": 1
        },
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "unit-test-invalid-001",
            "X-Hub-Signature-256": "sha256=bad",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


def test_tampered_webhook_body():
    original_body = b'{"action":"opened","issue":{"number":1}}'

    signature = make_signature(original_body)

    tampered_body = b'{"action":"closed","issue":{"number":1}}'

    response = client.post(
        "/webhook",
        content=tampered_body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "unit-test-tampered-001",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 401


def test_unknown_webhook_event():
    payload = {
        "action": "created"
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "unit-test-unknown-001",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported webhook event."
