import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Response

load_dotenv()

from app.github_client import create_issue, get_issue, list_issues
from app.models import IssueCreate

app = FastAPI(
    title="GitHub Issues Service",
    description="A REST service wrapping the GitHub Issues API.",
    version="1.0.0",
)


def format_issue(issue):
    return {
        "number": issue["number"],
        "html_url": issue["html_url"],
        "state": issue["state"],
        "title": issue["title"],
        "body": issue["body"],
        "labels": [
            label["name"]
            for label in issue.get("labels", [])
        ],
        "created_at": issue["created_at"],
        "updated_at": issue["updated_at"],
    }


@app.get("/")
async def root():
    return {
        "message": "GitHub Issues Service is running"
    }


@app.get("/healthz")
async def health_check():
    return {
        "status": "ok"
    }


@app.post("/issues", status_code=201)
async def post_issue(
    issue: IssueCreate,
    response: Response,
):
    github_issue = await create_issue(
        title=issue.title,
        body=issue.body,
        labels=issue.labels,
    )

    response.headers["Location"] = (
        f"/issues/{github_issue['number']}"
    )

    return format_issue(github_issue)


@app.get("/issues")
async def get_issues(
    response: Response,
    state: str = Query(
        default="open",
        pattern="^(open|closed|all)$",
    ),
    labels: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(
        default=30,
        ge=1,
        le=100,
    ),
):
    issues, link_header = await list_issues(
        state=state,
        labels=labels,
        page=page,
        per_page=per_page,
    )

    if link_header:
        response.headers["Link"] = link_header

    return [
        format_issue(issue)
        for issue in issues
        if "pull_request" not in issue
    ]


@app.get("/issues/{number}")
async def get_single_issue(number: int):
    issue = await get_issue(number)

    return format_issue(issue)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
