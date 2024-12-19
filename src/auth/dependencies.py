from typing import Any, List
from datetime import datetime

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.main import get_session
from src.db.models import User
from src.db.redis import token_in_logout

from .service import UserService
from .utils import decode_token
from src.errors import (
    InvalidToken,
    RevokedToken,
    InsufficientPermission,
    AccountNotVerified,
)

user_service = UserService()


class AccessTokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
            super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        cred = await super().__call__(request)

        token = cred.credentials

        token_data = decode_token(token)

        if await token_in_logout(token_data["jti"]):
            raise InvalidToken()

        # print(token_data)

        return token_data


async def get_refresh_id_from_cookie(request: Request):
    return request.cookies.get("refresh_id", None)


async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_email = token_details["user"]["email"]

    user = await user_service.get_user_by_email(user_email, session)

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        if not current_user.is_verified:
            raise AccountNotVerified()
        if current_user.role in self.allowed_roles:
            return True

        raise InsufficientPermission()
    