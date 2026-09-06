import os

from dotenv import load_dotenv
from fastapi import FastAPI, Response

load_dotenv()

from app.github_client import create_issue
from app.models import IssueCreate

app = FastAPI(
    title="GitHub Issues Service",
    description="A REST service wrapping the GitHub Issues API.",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "GitHub Issues Service is running"}


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}


@app.post("/issues", status_code=201)
async def post_issue(issue: IssueCreate, response: Response):
    github_issue = await create_issue(
        title=issue.title,
        body=issue.body,
        labels=issue.labels,
    )

    response.headers["Location"] = f"/issues/{github_issue['number']}"

    return {
        "number": github_issue["number"],
        "html_url": github_issue["html_url"],
        "state": github_issue["state"],
        "title": github_issue["title"],
        "body": github_issue["body"],
        "labels": [
            label["name"]
            for label in github_issue.get("labels", [])
        ],
        "created_at": github_issue["created_at"],
        "updated_at": github_issue["updated_at"],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
