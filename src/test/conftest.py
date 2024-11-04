import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from fakeredis import FakeAsyncRedis

from src.db.main import get_session
from src.auth.dependencies import get_current_user
from src.books.routes import access_token_bearer
from src.auth.routes import refresh_token_bearer
from src import app
from src.config import Config 
from src.test.utils import(
    get_mock_session,
    mock_book,
    mock_tag,
    mock_user,
    mock_token
)

# app.dependency_overrides[get_session] = get_mock_session


@pytest.fixture
def test_session():
    mock_session = get_mock_session()
    yield mock_session


@pytest_asyncio.fixture
async def redis_client():
    async with FakeAsyncRedis() as client:
        yield client


@pytest.fixture
def test_client():
    app.dependency_overrides[get_session] = get_mock_session
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_user():
    return mock_user()


@pytest.fixture
def test_book():
    return mock_book()


@pytest.fixture
def test_tag():
    return mock_tag()


@pytest.fixture
def test_verified_client(test_client):

    app.dependency_overrides[get_current_user] = mock_user

    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_book_client(test_client):
     
    app.dependency_overrides[get_current_user] = mock_user
    app.dependency_overrides[access_token_bearer] = mock_token

    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_fail_book_client(test_client):
     
    app.dependency_overrides[get_current_user] = mock_user
    # app.dependency_overrides[access_token_bearer] = mock_token

    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_fail_review_client(test_client):

    app.dependency_overrides[get_current_user] = mock_user
    # app.dependency_overrides[access_token_bearer] = mock_token

    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_tag_client(test_client):

    app.dependency_overrides[get_current_user] = mock_user

    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_refresh_token_client(test_client):

    app.dependency_overrides[refresh_token_bearer] = mock_token

    yield test_client

    app.dependency_overrides.clear()

# ======================================== (Message Queue Worker) ===================================

import logging
import os
import random

import pytest
import redis

import dramatiq
from dramatiq import Worker
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker


logfmt = "[%(asctime)s] [%(threadName)s] [%(name)s] [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=logfmt)
logging.getLogger("pika").setLevel(logging.WARN)

random.seed(1337)

CI = os.getenv("GITHUB_ACTION") or \
    os.getenv("APPVEYOR") == "true"


def check_redis(client):
    try:
        client.ping()
    except redis.ConnectionError as e:
        raise e if CI else pytest.skip("No connection to Redis server.") from None


@pytest.fixture()
def stub_broker():
    broker = StubBroker()
    broker.emit_after("process_boot")
    dramatiq.set_broker(broker)
    yield broker
    broker.flush_all()
    broker.close()


@pytest.fixture()
def redis_broker():
    broker = RedisBroker()
    check_redis(broker.client)
    broker.client.flushall()
    broker.emit_after("process_boot")
    dramatiq.set_broker(broker)
    yield broker
    broker.client.flushall()
    broker.close()


@pytest.fixture()
def stub_worker(stub_broker):
    worker = Worker(stub_broker, worker_timeout=100, worker_threads=32)
    worker.start()
    yield worker
    worker.stop()


@pytest.fixture()
def redis_worker(redis_broker):
    worker = Worker(redis_broker, worker_threads=32)
    worker.start()
    yield worker
    worker.stop()
