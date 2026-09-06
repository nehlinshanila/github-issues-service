# GitHub Issues Service

A production-style REST API built with **FastAPI** that wraps the **GitHub Issues REST API** for a single configured repository.

The service supports issue creation, retrieval, updates, comments, webhook processing, local event persistence, automated testing, OpenAPI 3.1 documentation, and Docker-based execution.

---

## Features

- Create GitHub issues
- List issues with filters and pagination
- Get a single issue
- Update issue title, body, or state
- Close and reopen issues
- Add comments to issues
- Receive GitHub webhooks
- Validate webhook signatures using HMAC SHA-256
- Handle `issues`, `issue_comment`, and `ping` webhook events
- Store webhook events locally using SQLite
- Deduplicate webhook deliveries
- Health check endpoint
- OpenAPI 3.1 API contract
- Swagger UI
- Docker support
- Unit tests
- Integration tests against the real GitHub API
- External API mocking for negative paths
- Pagination and GitHub error mapping

---

## Tech Stack

- Python 3
- FastAPI
- HTTPX
- Pydantic
- SQLite
- Pytest
- pytest-asyncio
- pytest-cov
- Docker
- GitHub REST API
- GitHub Webhooks
- OpenAPI 3.1

---

## Project Structure

```text
github-issues-service/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── github_client.py
│   ├── models.py
│   ├── database.py
│   └── webhook.py
│
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_github_client.py
│   ├── test_integration.py
│   ├── test_issues.py
│   ├── test_utils.py
│   └── test_webhook.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── design-note.md
├── openapi.yaml
├── requirements.txt
└── webhook_test.json
```

---

## Environment Variables

Create a `.env` file in the project root.

```env
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name
WEBHOOK_SECRET=your_webhook_secret
PORT=8000
```

### Variable Description

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | Fine-grained GitHub personal access token |
| `GITHUB_OWNER` | GitHub username or repository owner |
| `GITHUB_REPO` | Repository used by the service |
| `WEBHOOK_SECRET` | Shared secret used for webhook HMAC validation |
| `PORT` | Port on which the application runs |

The real `.env` file must never be committed.

Use `.env.example` as a template.

---

## GitHub Token Permissions

The fine-grained GitHub token should be scoped only to the repository used by this project.

Required permission:

```text
Issues: Read and Write
```

Minimizing token permissions follows the principle of least privilege.

---

# Running Locally Without Docker

## 1. Clone the Repository

```bash
git clone https://github.com/nehlinshanila/github-issues-service.git
cd github-issues-service
```

## 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Create `.env`

```bash
cp .env.example .env
```

Then edit `.env` and add the required values.

## 5. Run the Application

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

---

# Running with Docker

## Build the Image

```bash
docker build -t github-issues-service .
```

## Run the Container

```bash
docker run --rm -p 8001:8000 \
  --env-file .env \
  github-issues-service
```

The service will then be available at:

```text
http://127.0.0.1:8001
```

Swagger UI:

```text
http://127.0.0.1:8001/docs
```

Health check:

```text
http://127.0.0.1:8001/healthz
```

Expected response:

```json
{
  "status": "ok"
}
```

---

# API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service root |
| GET | `/healthz` | Health check |
| POST | `/issues` | Create an issue |
| GET | `/issues` | List issues |
| GET | `/issues/{number}` | Get one issue |
| PATCH | `/issues/{number}` | Update an issue |
| POST | `/issues/{number}/comments` | Add a comment |
| POST | `/webhook` | Receive a GitHub webhook |
| GET | `/events` | List stored webhook events |

---

# API Examples

## Create an Issue

```bash
curl -X POST http://127.0.0.1:8000/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Example issue from FastAPI",
    "body": "This issue was created through the GitHub Issues Service.",
    "labels": []
  }'
```

Expected success status:

```text
201 Created
```

The response includes:

```json
{
  "number": 1,
  "html_url": "https://github.com/OWNER/REPO/issues/1",
  "state": "open",
  "title": "Example issue from FastAPI",
  "body": "This issue was created through the GitHub Issues Service.",
  "labels": [],
  "created_at": "...",
  "updated_at": "..."
}
```

The service also returns a `Location` header:

```text
/issues/{number}
```

---

## List Issues

```bash
curl "http://127.0.0.1:8000/issues?state=open&page=1&per_page=30"
```

Supported query parameters:

```text
state=open|closed|all
labels=label1,label2
page=1
per_page=30
```

Maximum `per_page` value:

```text
100
```

GitHub pagination semantics are preserved.

---

## Get a Single Issue

```bash
curl http://127.0.0.1:8000/issues/1
```

Expected success:

```text
200 OK
```

If the issue does not exist:

```text
404 Not Found
```

---

## Update an Issue

Update title and body:

```bash
curl -X PATCH http://127.0.0.1:8000/issues/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated issue title",
    "body": "Updated through the FastAPI service."
  }'
```

Close an issue:

```bash
curl -X PATCH http://127.0.0.1:8000/issues/1 \
  -H "Content-Type: application/json" \
  -d '{
    "state": "closed"
  }'
```

Reopen an issue:

```bash
curl -X PATCH http://127.0.0.1:8000/issues/1 \
  -H "Content-Type: application/json" \
  -d '{
    "state": "open"
  }'
```

GitHub does not support deleting issues, so closing an issue is used as the delete-equivalent operation.

---

## Add a Comment

```bash
curl -X POST http://127.0.0.1:8000/issues/1/comments \
  -H "Content-Type: application/json" \
  -d '{
    "body": "This comment was created through my FastAPI GitHub Issues Service."
  }'
```

Expected response:

```text
201 Created
```

Example response:

```json
{
  "id": 123456789,
  "body": "This comment was created through my FastAPI GitHub Issues Service.",
  "user": "username",
  "created_at": "...",
  "html_url": "https://github.com/OWNER/REPO/issues/1#issuecomment-..."
}
```

---

# Webhook Handling

The service provides:

```text
POST /webhook
```

GitHub sends webhook events to this endpoint.

The implementation:

- reads the raw request body
- obtains `X-Hub-Signature-256`
- calculates HMAC SHA-256 using `WEBHOOK_SECRET`
- performs constant-time signature comparison
- identifies the GitHub event
- extracts the event action
- stores the event locally
- prevents duplicate processing

Supported events:

```text
issues
issue_comment
ping
```

Successful requests return:

```text
204 No Content
```

Invalid signature:

```text
401 Unauthorized
```

Unsupported event or action:

```text
400 Bad Request
```

---

# Webhook Setup on GitHub

Open the GitHub repository and go to:

```text
Settings
→ Webhooks
→ Add webhook
```

Use the following configuration.

### Payload URL

For local testing, expose the FastAPI server using a public tunnel.

Example using Cloudflare Tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare will provide a temporary public URL such as:

```text
https://example.trycloudflare.com
```

Webhook payload URL:

```text
https://example.trycloudflare.com/webhook
```

### Content Type

```text
application/json
```

### Secret

Use the exact same value as:

```env
WEBHOOK_SECRET=your_webhook_secret
```

### Events

Select:

```text
Issues
Issue comments
```

GitHub also sends a `ping` event when the webhook is created.

---

# Webhook Redelivery

To redeliver a webhook:

```text
GitHub Repository
→ Settings
→ Webhooks
→ Select the webhook
→ Recent Deliveries
→ Select a delivery
→ Redeliver
```

The service uses GitHub's delivery ID and action information for retry-safe and duplicate-safe handling.

---

# Stored Webhook Events

Webhook events are persisted locally using SQLite.

View recent events:

```bash
curl http://127.0.0.1:8000/events
```

Optional limit:

```bash
curl "http://127.0.0.1:8000/events?limit=20"
```

Example response:

```json
[
  {
    "delivery_id": "example-delivery-id",
    "event": "issue_comment",
    "action": "created",
    "issue_number": 1,
    "timestamp": "2026-09-06T05:50:52+00:00"
  }
]
```

---

# Error Handling

GitHub API errors are translated into appropriate service responses.

Examples:

| GitHub Status | Service Status |
|---|---|
| 401 | 401 Unauthorized |
| 403 | 403 Forbidden |
| 404 | 404 Not Found |
| 422 | 400 Bad Request |

Invalid local request payloads are also rejected with clear validation messages.

---

# Pagination

The service supports:

```text
page
per_page
```

and preserves GitHub pagination behavior.

The GitHub `Link` response header is parsed so next and previous pagination URLs can be identified.

Example:

```bash
curl "http://127.0.0.1:8000/issues?page=1&per_page=30"
```

---

# Rate Limits and Reliability

The GitHub client forwards and interprets GitHub API failures.

The service is designed to surface meaningful errors for:

- authorization failures
- permission failures
- missing resources
- validation failures
- rate limiting
- upstream GitHub API problems

Webhook processing returns quickly and persists event metadata locally.

---

# OpenAPI 3.1 Contract

The repository includes:

```text
openapi.yaml
```

The specification uses:

```yaml
openapi: 3.1.0
```

The contract documents:

- API routes
- request bodies
- response structures
- success responses
- error responses
- reusable schemas
- examples
- authentication requirements

Reusable schemas include objects for:

- issues
- issue creation
- issue updates
- comments
- webhook events
- errors

Swagger UI is also automatically available through FastAPI:

```text
http://127.0.0.1:8000/docs
```

---

# Testing

The project includes both unit and integration tests.

Test files:

```text
tests/test_database.py
tests/test_github_client.py
tests/test_integration.py
tests/test_issues.py
tests/test_utils.py
tests/test_webhook.py
```

---

## Run Unit Tests

```bash
pytest -v
```

The real GitHub integration test is skipped during a normal test run to avoid creating real GitHub resources every time tests are executed.

Example result:

```text
26 passed, 1 skipped
```

---

## Run Real GitHub Integration Test

```bash
RUN_GITHUB_INTEGRATION=1 pytest tests/test_integration.py -v
```

The integration test interacts with the configured GitHub test repository.

It verifies an end-to-end GitHub API workflow.

---

## Test Coverage

Run:

```bash
pytest --cov=app --cov-report=term-missing
```

Current project coverage:

```text
86%
```

This exceeds the assignment target of:

```text
>= 80%
```

---

# Tested Behaviors

The automated test suite covers:

- request validation
- missing issue title
- empty title
- invalid issue state
- invalid pagination values
- health endpoint
- GitHub API calls
- GitHub authentication headers
- issue creation
- issue listing
- issue retrieval
- issue updates
- partial updates
- comments
- GitHub error translation
- pagination Link header parsing
- webhook signature validation
- invalid webhook signatures
- tampered webhook payloads
- unsupported webhook events
- SQLite event storage
- event deduplication
- event limits
- real GitHub integration

---

# Webhook Security

Webhook authenticity is validated using:

```text
HMAC SHA-256
```

The service compares signatures using a constant-time comparison to reduce timing-attack risk.

Secrets are loaded through environment variables and are never hard-coded into source code.

The application does not intentionally log:

- GitHub tokens
- webhook secrets
- raw webhook signatures

---

# Docker Verification

The Docker image can be built successfully using:

```bash
docker build -t github-issues-service .
```

Run it using:

```bash
docker run --rm -p 8001:8000 \
  --env-file .env \
  github-issues-service
```

Verify:

```bash
curl http://127.0.0.1:8001/healthz
```

Expected output:

```json
{
  "status": "ok"
}
```

---

# Design Notes

A short engineering design document is included in:

```text
design-note.md
```

It discusses:

- GitHub error mapping
- pagination strategy
- webhook deduplication
- webhook security
- persistence
- implementation trade-offs

---

# HTTP Semantics

The service follows appropriate HTTP behavior.

Examples:

```text
POST /issues
→ 201 Created
```

```text
POST /issues/{number}/comments
→ 201 Created
```

```text
POST /webhook
→ 204 No Content
```

```text
GET /issues/{number}
→ 404 Not Found when the issue does not exist
```

---

# Security Practices

- Fine-grained GitHub token
- Minimum repository permissions
- Environment-based configuration
- `.env` excluded from Git
- HMAC SHA-256 webhook validation
- Constant-time signature comparison
- No hard-coded tokens
- No committed secrets
- Public `.env.example` contains placeholders only

---

# Example `.env.example`

```env
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name
WEBHOOK_SECRET=your_webhook_secret
PORT=8000
```

---

# Author

**Shanila Nehlin**

CMPE GitHub Service Assignment

Implementation, tests, API specification, documentation, webhook processing, and Docker configuration prepared for the GitHub Issues Service project.

---

# Repository

```text
https://github.com/nehlinshanila/github-issues-service
```
