import httpx
import pytest
from fastapi import HTTPException

from app.github_client import handle_github_error


def make_response(status_code: int, body=None):
    request = httpx.Request(
        "GET",
        "https://api.github.com/test"
    )

    if body is None:
        return httpx.Response(
            status_code=status_code,
            request=request,
        )

    return httpx.Response(
        status_code=status_code,
        json=body,
        request=request,
    )


def test_github_401_maps_to_401():
    response = make_response(
        401,
        {"message": "Bad credentials"},
    )

    with pytest.raises(HTTPException) as exc:
        handle_github_error(response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "GitHub authentication failed."


def test_github_403_maps_to_403():
    response = make_response(
        403,
        {"message": "Forbidden"},
    )

    with pytest.raises(HTTPException) as exc:
        handle_github_error(response)

    assert exc.value.status_code == 403
    assert exc.value.detail == (
        "GitHub denied access or rate limit exceeded."
    )


def test_github_404_maps_to_404():
    response = make_response(
        404,
        {"message": "Not Found"},
    )

    with pytest.raises(HTTPException) as exc:
        handle_github_error(response)

    assert exc.value.status_code == 404
    assert exc.value.detail == "GitHub resource not found."


def test_github_422_maps_to_400():
    response = make_response(
        422,
        {
            "message": "Validation Failed"
        },
    )

    with pytest.raises(HTTPException) as exc:
        handle_github_error(response)

    assert exc.value.status_code == 400


def parse_link_header(link_header: str):
    links = {}

    if not link_header:
        return links

    parts = link_header.split(",")

    for part in parts:
        section = part.strip().split(";")

        if len(section) != 2:
            continue

        url = section[0].strip()[1:-1]
        rel = section[1].strip()

        if 'rel="' in rel:
            rel_name = rel.split('rel="')[1].split('"')[0]
            links[rel_name] = url

    return links


def test_parse_link_header_next_and_last():
    header = (
        '<https://api.github.com/repos/test/issues?page=2>; rel="next", '
        '<https://api.github.com/repos/test/issues?page=5>; rel="last"'
    )

    result = parse_link_header(header)

    assert result["next"].endswith("page=2")
    assert result["last"].endswith("page=5")


def test_parse_link_header_empty():
    assert parse_link_header("") == {}
