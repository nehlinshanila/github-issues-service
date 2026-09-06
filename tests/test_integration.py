# Author: Shanila Nehlin
# CMPE 272 - HW #2: GitHub Service
# Integration tests using the running FastAPI service and real GitHub test repository.

import os
import time

import httpx
import pytest
from dotenv import load_dotenv


load_dotenv(".env")

BASE_URL = os.getenv("INTEGRATION_BASE_URL", "http://127.0.0.1:8000")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

RUN_INTEGRATION = os.getenv("RUN_GITHUB_INTEGRATION") == "1"


pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="Set RUN_GITHUB_INTEGRATION=1 to run real GitHub integration tests.",
)


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_github_issue_end_to_end():
    assert GITHUB_TOKEN, "GITHUB_TOKEN is missing from .env"
    assert GITHUB_OWNER, "GITHUB_OWNER is missing from .env"
    assert GITHUB_REPO, "GITHUB_REPO is missing from .env"

    unique = int(time.time())

    # ---------------------------------------------------------
    # 1. CREATE ISSUE THROUGH OUR FASTAPI SERVICE
    # ---------------------------------------------------------
    create_response = httpx.post(
        f"{BASE_URL}/issues",
        json={
            "title": f"Integration Test Issue {unique}",
            "body": "Created automatically by integration test.",
            "labels": [],
        },
        timeout=30.0,
    )

    assert create_response.status_code == 201

    created_issue = create_response.json()
    issue_number = created_issue["number"]

    assert created_issue["title"] == f"Integration Test Issue {unique}"
    assert created_issue["state"] == "open"

    # Verify Location header
    assert create_response.headers["location"] == f"/issues/{issue_number}"

    # ---------------------------------------------------------
    # 2. GET THE CREATED ISSUE
    # ---------------------------------------------------------
    get_response = httpx.get(
        f"{BASE_URL}/issues/{issue_number}",
        timeout=30.0,
    )

    assert get_response.status_code == 200

    fetched_issue = get_response.json()

    assert fetched_issue["number"] == issue_number
    assert fetched_issue["state"] == "open"

    # ---------------------------------------------------------
    # 3. UPDATE TITLE AND BODY
    # ---------------------------------------------------------
    update_response = httpx.patch(
        f"{BASE_URL}/issues/{issue_number}",
        json={
            "title": f"Updated Integration Test {unique}",
            "body": "Issue body updated through FastAPI integration test.",
        },
        timeout=30.0,
    )

    assert update_response.status_code == 200

    updated_issue = update_response.json()

    assert updated_issue["title"] == f"Updated Integration Test {unique}"
    assert (
        updated_issue["body"]
        == "Issue body updated through FastAPI integration test."
    )

    # ---------------------------------------------------------
    # 4. CLOSE ISSUE
    # ---------------------------------------------------------
    close_response = httpx.patch(
        f"{BASE_URL}/issues/{issue_number}",
        json={
            "state": "closed",
        },
        timeout=30.0,
    )

    assert close_response.status_code == 200
    assert close_response.json()["state"] == "closed"

    # ---------------------------------------------------------
    # 5. REOPEN ISSUE
    # ---------------------------------------------------------
    reopen_response = httpx.patch(
        f"{BASE_URL}/issues/{issue_number}",
        json={
            "state": "open",
        },
        timeout=30.0,
    )

    assert reopen_response.status_code == 200
    assert reopen_response.json()["state"] == "open"

    # ---------------------------------------------------------
    # 6. CREATE COMMENT THROUGH OUR SERVICE
    # ---------------------------------------------------------
    comment_text = f"Integration test comment {unique}"

    comment_response = httpx.post(
        f"{BASE_URL}/issues/{issue_number}/comments",
        json={
            "body": comment_text,
        },
        timeout=30.0,
    )

    assert comment_response.status_code == 201

    created_comment = comment_response.json()

    assert created_comment["body"] == comment_text
    assert "id" in created_comment
    assert "user" in created_comment
    assert "created_at" in created_comment
    assert "html_url" in created_comment

    # ---------------------------------------------------------
    # 7. FETCH COMMENT LIST DIRECTLY FROM GITHUB
    # ---------------------------------------------------------
    github_comments_url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/issues/"
        f"{issue_number}/comments"
    )

    comments_response = httpx.get(
        github_comments_url,
        headers=github_headers(),
        timeout=30.0,
    )

    assert comments_response.status_code == 200

    comments = comments_response.json()

    assert any(
        comment["body"] == comment_text
        for comment in comments
    )

    # ---------------------------------------------------------
    # 8. FINAL CLEANUP: CLOSE TEST ISSUE
    # ---------------------------------------------------------
    cleanup_response = httpx.patch(
        f"{BASE_URL}/issues/{issue_number}",
        json={
            "state": "closed",
        },
        timeout=30.0,
    )

    assert cleanup_response.status_code == 200
    assert cleanup_response.json()["state"] == "closed"
