from unittest.mock import Mock, AsyncMock
from datetime import datetime, date, timedelta
from src.auth.utils import generate_passwd_hash

mock_session = AsyncMock()

def get_mock_session():
    yield mock_session


def mock_user():
    return Mock(
        uid="test123",
        username="john_doe",
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
        is_verified=True,
        role="user",
        password_hash=generate_passwd_hash("secret"),
        created_at=datetime.now(),
        update_at=datetime.now(),
        books=[],
        reviews=[]
    )

def mock_book():
    return Mock(
        uid="test123",
        title="sample title",
        author="same author",
        publisher="same publisher",
        published_date=date.today(),
        description="sample description",
        page_count=200,
        language="English",
        created_at=datetime.now(),
        update_at=datetime.now()
    )


def mock_tag():
    mock_tag = Mock(spec_set=['uid', 'name', 'created_at'])
    mock_tag.configure_mock(uid="test123", name="Art", created_at=datetime.now())
    return mock_tag


def mock_token():
    token = {}
    user_data = dict(
        email="john.doe@example.com",
        user_uid="test123",
        role="user"
    )
    token["user"] = user_data
    token["exp"] = (datetime.now() + timedelta(seconds=3600)).timestamp()
    return token
