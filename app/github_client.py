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


def handle_github_error(response: httpx.Response):
    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="GitHub authentication failed.",
        )

    if response.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="GitHub denied access or rate limit exceeded.",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="GitHub resource not found.",
        )

    if response.status_code == 422:
        raise HTTPException(
            status_code=400,
            detail=response.json(),
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )


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

    handle_github_error(response)
    return response.json()


async def list_issues(
    state: str = "open",
    labels: str | None = None,
    page: int = 1,
    per_page: int = 30,
):
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"

    params = {
        "state": state,
        "page": page,
        "per_page": per_page,
    }

    if labels:
        params["labels"] = labels

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_headers(),
            params=params,
        )

    handle_github_error(response)

    return response.json(), response.headers.get("Link")


async def get_issue(number: int):
    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/issues/{number}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_headers(),
        )

    handle_github_error(response)

    return response.json()
