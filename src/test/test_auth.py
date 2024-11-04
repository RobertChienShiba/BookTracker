import pytest
from unittest.mock import patch

auth_prefix = f"/api/v1/auth"

@patch("src.auth.service.UserService.get_user_by_email")
def test_login_success(mock_user, test_client, test_user, test_session):

    mock_user.return_value = test_user
    
    login_data = {
        "email": "test@example.com",
        "password": "secret"
    }
    
    response = test_client.post(f"{auth_prefix}/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "access_token" in data
    assert "refresh_token" in data

    assert mock_user.called_once_with(login_data["email"], test_session)


@patch("src.auth.service.UserService.get_user_by_email")
def test_login_fail_invalid_password(mock_get_user, test_client, test_user, test_session):

    mock_get_user.return_value = test_user

    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }

    response = test_client.post(f"{auth_prefix}/login", json=login_data)

    assert response.status_code == 400
    data = response.json()
    assert data["message"] == "Invalid Email Or Password"

    assert mock_get_user.called_once_with(login_data["email"], test_session)


def test_user_verified(test_verified_client):
    response = test_verified_client.get(f"{auth_prefix}/me", headers={"Authorization": "Bearer " + 'fake.jwt'})
    assert response.status_code == 200
    result = response.json()
    assert result["is_verified"] is True


def test_refresh_token(test_refresh_token_client):
    response = test_refresh_token_client.get(f"{auth_prefix}/refresh_token", headers={"Authorization": "Bearer " + 'fake.jwt'})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_send_mail(test_client):
    test_email = {"email": "test@example.com"}

    with patch("src.bg_task.send_email.send") as mock_send_email:
        mock_send_email.return_value = None

        response = test_client.post(f"{auth_prefix}/send_mail", json=test_email)

        assert response.status_code == 200
        assert response.json() == {"message": "test@example.com sent successfully"}

        mock_send_email.assert_called_once_with(
            ["test@example.com"], "Welcome to our app", "<h1>Welcome to the app</h1>"
        )
