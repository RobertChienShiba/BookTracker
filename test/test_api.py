import pytest
from unittest.mock import patch
from datetime import date
import asyncio

from src import version_prefix


@patch("src.books.service.BookService.create_book")
def test_create_cook(mock_create_book, test_book_client, test_book):

    book_data = dict(
        title = "hello world",
        author = "shohei ohtani",
        publisher = "mlb",
        published_date = date.today().strftime('%Y-%m-%d'),
        page_count = 250,
        language = "Japanese"
    )

    mock_create_book.return_value = test_book
    response = test_book_client.post(f"{version_prefix}/books/", json=book_data, headers={"Authorization": "Bearer " + 'fake.jwt'})

    assert response.status_code == 201
    assert mock_create_book.called_once()


@patch("src.books.service.BookService.create_book")
def test_fail_create_cook(mock_create_book, test_fail_book_client, test_book):

    book_data = dict(
        title = "hello world",
        author = "shohei ohtani",
        publisher = "mlb",
        published_date = date.today().strftime('%Y-%m-%d'),
        page_count = 250,
        language = "Japanese"
    )

    mock_create_book.return_value = test_book

    response = test_fail_book_client.post(f"{version_prefix}/books/", json=book_data, headers={"Authorization": "Bearer " + 'fake.jwt'})

    assert response.status_code == 401
    assert mock_create_book.called_once()


def test_fail_all_review(test_fail_review_client):
    response = test_fail_review_client.get(f"{version_prefix}/reviews/")
    assert response.status_code == 401
    data = response.json()
    assert data["message"] == "You do not have enough permissions to perform this action"


@patch("src.tags.service.TagService.add_tag")
def test_add_book_tag(mock_add_tag, test_tag, test_tag_client, test_session):

    mock_add_tag.return_value = test_tag

    tag_data = {"name": "Science"}

    response = test_tag_client.post(f"{version_prefix}/tags/", json=tag_data)
    assert response.status_code == 201
    assert mock_add_tag.called_once_with(tag_data, test_session)


@pytest.mark.asyncio
async def test_add_jti_to_logout(redis_client):

    await redis_client.set(name="test_jti", value="test", ex=20)

    target = await redis_client.get("test_jti")

    assert target == b"test"

    await asyncio.sleep(20)

    exist = await redis_client.exists("test_jti")

    assert exist == 0
