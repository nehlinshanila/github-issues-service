# GitHub Issues Service

A REST API service built with FastAPI that wraps the GitHub Issues API.

## Features

- Create GitHub issues
- List issues with filters and pagination
- Get a single issue
- Update issue title, body, or state
- Add comments to issues
- Receive and validate GitHub webhooks
- Store webhook events
- Health check endpoint
- OpenAPI documentation
- Docker support
- Automated tests with pytest

## Tech Stack

- Python
- FastAPI
- HTTPX
- SQLite
- Pytest
- Docker
- GitHub REST API

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service root |
| GET | `/healthz` | Health check |
| POST | `/issues` | Create an issue |
| GET | `/issues` | List issues |
| GET | `/issues/{number}` | Get one issue |
| PATCH | `/issues/{number}` | Update an issue |
| POST | `/issues/{number}/comments` | Add a comment |
| POST | `/webhook` | Receive GitHub webhook |
| GET | `/events` | List stored webhook events |

## Environment Variables

Create a `.env` file:

```env
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=github-issues-service
WEBHOOK_SECRET=your_webhook_secret
