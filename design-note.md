# Design Note

## Architecture

The service is implemented using FastAPI and acts as a lightweight wrapper around the GitHub Issues REST API.

The application is divided into several modules:

- `main.py` defines the HTTP endpoints.
- `github_client.py` handles communication with GitHub.
- `models.py` defines request validation models.
- `webhook.py` validates webhook signatures.
- `database.py` stores webhook delivery events.

## GitHub API Integration

The service authenticates to GitHub using a fine-grained personal access token.

The token is loaded from environment variables and is not stored in source code.

HTTP requests are made asynchronously using HTTPX.

## Validation

Pydantic models validate incoming issue and comment payloads.

Invalid client payloads are converted into HTTP 400 responses.

GitHub API errors are mapped into appropriate HTTP response codes.

## Webhooks

GitHub webhook requests are authenticated using an HMAC SHA-256 signature.

The signature received in the `X-Hub-Signature-256` header is compared with a locally generated signature using the configured webhook secret.

Invalid signatures are rejected with HTTP 401.

Valid webhook deliveries are stored in SQLite.

Duplicate deliveries are prevented using the GitHub delivery identifier.

## Testing

The project uses pytest.

Tests cover:

- request validation
- GitHub API error mappings
- GitHub client behavior
- webhook signature validation
- tampered webhook bodies
- unknown webhook events
- database event storage
- event deduplication
- health endpoint

The current test suite contains 26 passing tests with approximately 86% total code coverage.

## Docker

The application is containerized using a Python slim base image.

The container installs dependencies, copies the source code, and runs Uvicorn on port 8000.

Secrets are supplied at runtime using environment variables rather than being included in the image.
