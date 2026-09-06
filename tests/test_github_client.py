import pytest

import app.github_client as github_client


class FakeResponse:
    def __init__(
        self,
        status_code=200,
        json_data=None,
        headers=None,
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json_data


class FakeAsyncClient:
    response = None
    last_method = None
    last_url = None
    last_headers = None
    last_json = None
    last_params = None

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    async def post(
        self,
        url,
        headers=None,
        json=None,
    ):
        FakeAsyncClient.last_method = "POST"
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_headers = headers
        FakeAsyncClient.last_json = json

        return FakeAsyncClient.response

    async def get(
        self,
        url,
        headers=None,
        params=None,
    ):
        FakeAsyncClient.last_method = "GET"
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_headers = headers
        FakeAsyncClient.last_params = params

        return FakeAsyncClient.response

    async def patch(
        self,
        url,
        headers=None,
        json=None,
    ):
        FakeAsyncClient.last_method = "PATCH"
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_headers = headers
        FakeAsyncClient.last_json = json

        return FakeAsyncClient.response


@pytest.fixture(autouse=True)
def mock_async_client(monkeypatch):
    monkeypatch.setattr(
        github_client.httpx,
        "AsyncClient",
        FakeAsyncClient,
    )


def test_get_headers():
    headers = github_client.get_headers()

    assert "Authorization" in headers
    assert headers["Accept"] == "application/vnd.github+json"


@pytest.mark.asyncio
async def test_create_issue():
    FakeAsyncClient.response = FakeResponse(
        status_code=201,
        json_data={
            "number": 10,
            "title": "Test issue",
        },
    )

    result = await github_client.create_issue(
        title="Test issue",
        body="Issue body",
        labels=["bug"],
    )

    assert result["number"] == 10
    assert FakeAsyncClient.last_method == "POST"

    assert FakeAsyncClient.last_json == {
        "title": "Test issue",
        "body": "Issue body",
        "labels": ["bug"],
    }


@pytest.mark.asyncio
async def test_list_issues():
    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        json_data=[
            {
                "number": 1,
                "title": "Issue 1",
            }
        ],
        headers={
            "Link": (
                '<https://api.github.com/test?page=2>; '
                'rel="next"'
            )
        },
    )

    issues, link = await github_client.list_issues(
        state="open",
        labels="bug",
        page=1,
        per_page=30,
    )

    assert len(issues) == 1
    assert issues[0]["number"] == 1
    assert "rel=\"next\"" in link

    assert FakeAsyncClient.last_params["state"] == "open"
    assert FakeAsyncClient.last_params["labels"] == "bug"
    assert FakeAsyncClient.last_params["page"] == 1
    assert FakeAsyncClient.last_params["per_page"] == 30


@pytest.mark.asyncio
async def test_get_issue():
    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        json_data={
            "number": 1,
            "title": "Existing issue",
        },
    )

    result = await github_client.get_issue(1)

    assert result["number"] == 1
    assert FakeAsyncClient.last_method == "GET"
    assert FakeAsyncClient.last_url.endswith(
        "/issues/1"
    )


@pytest.mark.asyncio
async def test_update_issue_all_fields():
    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        json_data={
            "number": 1,
            "title": "Updated",
            "body": "Updated body",
            "state": "closed",
        },
    )

    result = await github_client.update_issue(
        number=1,
        title="Updated",
        body="Updated body",
        state="closed",
    )

    assert result["state"] == "closed"

    assert FakeAsyncClient.last_json == {
        "title": "Updated",
        "body": "Updated body",
        "state": "closed",
    }


@pytest.mark.asyncio
async def test_update_issue_partial():
    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        json_data={
            "number": 1,
            "state": "open",
        },
    )

    await github_client.update_issue(
        number=1,
        state="open",
    )

    assert FakeAsyncClient.last_json == {
        "state": "open"
    }


@pytest.mark.asyncio
async def test_create_comment():
    FakeAsyncClient.response = FakeResponse(
        status_code=201,
        json_data={
            "id": 123,
            "body": "Test comment",
        },
    )

    result = await github_client.create_comment(
        number=1,
        body="Test comment",
    )

    assert result["id"] == 123

    assert FakeAsyncClient.last_json == {
        "body": "Test comment"
    }

    assert FakeAsyncClient.last_url.endswith(
        "/issues/1/comments"
    )
