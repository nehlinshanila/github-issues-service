import os

import httpx
from fastapi import HTTPException

GITHUB_API = "https://api.github.com"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")


def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def create_issue(
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
):
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"

    payload = {"title": title}

    if body is not None:
        payload["body"] = body

    if labels is not None:
        payload["labels"] = labels

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=get_headers(),
            json=payload,
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="GitHub authentication failed.",
        )

    if response.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="GitHub denied access.",
        )

    if response.status_code == 422:
        raise HTTPException(
            status_code=400,
            detail=response.json(),
        )

    if response.status_code != 201:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()
