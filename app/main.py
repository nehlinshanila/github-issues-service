import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response

load_dotenv()

from app.database import get_events, init_db, save_event
from app.github_client import (
    create_comment,
    create_issue,
    get_issue,
    list_issues,
    update_issue,
)
from app.models import CommentCreate, IssueCreate, IssueUpdate
from app.webhook import verify_signature

app = FastAPI(
    title="GitHub Issues Service",
    description="A REST service wrapping the GitHub Issues API.",
    version="1.0.0",
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Invalid request.",
            "errors": exc.errors(),
        },
    )

@app.on_event("startup")
def startup_event():
    init_db()


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


@app.patch("/issues/{number}")
async def patch_issue(
    number: int,
    update: IssueUpdate,
):
    github_issue = await update_issue(
        number=number,
        title=update.title,
        body=update.body,
        state=update.state,
    )

    return format_issue(github_issue)


@app.post("/issues/{number}/comments", status_code=201)
async def post_comment(
    number: int,
    comment: CommentCreate,
):
    github_comment = await create_comment(
        number=number,
        body=comment.body,
    )

    return {
        "id": github_comment["id"],
        "body": github_comment["body"],
        "user": github_comment["user"]["login"],
        "created_at": github_comment["created_at"],
        "html_url": github_comment["html_url"],
    }


@app.post("/webhook", status_code=204)
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
):
    raw_body = await request.body()

    if not verify_signature(
        raw_body,
        x_hub_signature_256,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature.",
        )

    if not x_github_event:
        raise HTTPException(
            status_code=400,
            detail="Missing X-GitHub-Event header.",
        )

    allowed_events = {
        "issues",
        "issue_comment",
        "ping",
    }

    if x_github_event not in allowed_events:
        raise HTTPException(
            status_code=400,
            detail="Unsupported webhook event.",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )

    if x_github_event == "ping":
        action = "ping"
        issue_number = None

    else:
        action = payload.get("action")

        if not action:
            raise HTTPException(
                status_code=400,
                detail="Missing webhook action.",
            )

        issue = payload.get("issue", {})
        issue_number = issue.get("number")

    delivery_id = x_github_delivery or "unknown"

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    save_event(
        delivery_id=delivery_id,
        event=x_github_event,
        action=action,
        issue_number=issue_number,
        timestamp=timestamp,
    )

    return Response(status_code=204)


@app.get("/events")
async def list_webhook_events(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    )
):
    return get_events(limit)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
