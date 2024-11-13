import logging
import uuid
from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer
from fastapi import Depends, HTTPException, status

import jwt
from passlib.context import CryptContext

from src.config import Config

passwd_context = CryptContext(schemes=["bcrypt"])

ACCESS_TOKEN_EXPIRY = 600

serializer = URLSafeTimedSerializer(
    secret_key=Config.JWT_SECRET, salt="email-configuration"
)


def generate_passwd_hash(password: str) -> str:
    return passwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return passwd_context.verify(password, hash)


def create_access_token(
    user_data: dict, jti: uuid.UUID, expiry: timedelta = None
):
    payload = {}

    payload["user"] = user_data
    payload["exp"] = datetime.now(timezone.utc) + (
        timedelta(seconds=ACCESS_TOKEN_EXPIRY)
    )
    payload["jti"] = jti

    # print(payload["exp"])

    token = jwt.encode(
        payload=payload, key=Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM
    )

    return token


def decode_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = jwt.decode(
            jwt=token, key=Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM],
            options={"verify_exp": False}
        )

        return token_data

    except jwt.PyJWTError:
        raise credentials_exception


def create_url_safe_token(data: dict):

    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token:str):
    try:
        token_data = serializer.loads(token)

        return token_data
    
    except Exception as e:
        logging.error(str(e))
        