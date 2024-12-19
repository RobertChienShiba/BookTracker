import uuid

from fastapi import APIRouter, Depends, status, BackgroundTasks, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.db.redis import add_jti_to_logout, remove_jti_from_logout, token_in_logout

from .dependencies import (
    AccessTokenBearer,
    RoleChecker,
    get_current_user,
    get_refresh_id_from_cookie,
)
from .schemas import (
    UserBooksModel,
    UserCreateModel,
    UserLoginModel,
    EmailModel,
    PasswordResetConfirmModel,
)
from .service import UserService
from .utils import (
    create_access_token,
    verify_password,
    generate_passwd_hash,
    create_url_safe_token,
    decode_url_safe_token,
    ACCESS_TOKEN_EXPIRY,
)
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from src.config import Config
from src.db.main import get_session
from src.bg_task import send_email

auth_router = APIRouter()
user_service = UserService()
access_token_bearer = AccessTokenBearer()
role_checker = RoleChecker(["admin", "user"])
version = "1.1.1"


@auth_router.post("/send_mail", include_in_schema=False)
async def send_mail(emails: EmailModel):
    emails = emails.email

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    send_email.send([emails], subject, html)

    return {"message": f"{emails} sent successfully"}


@auth_router.post("/resend_verify_mail", status_code=status.HTTP_200_OK)
async def resend_mail(emails: EmailModel):
    email = emails.email

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}:{Config.APP_PORT}/api/{version}/auth/verify/{token}"

    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """

    subject = "Verify Your email"

    send_email.send([email], subject, html)

    return {"message": "Email resent successfully"}


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_Account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session),
):
    """
    Create user account using email, username, first_name, last_name
    params:
        user_data: UserCreateModel
    """
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise UserAlreadyExists()

    new_user = await user_service.create_user(user_data, session)

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}:{Config.APP_PORT}/api/{version}/auth/verify/{token}"

    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """

    subject = "Verify Your email"

    send_email.send([email], subject, html)

    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }


@auth_router.get("/verify/{token}", include_in_schema=False)
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email", None)

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"is_verified": True}, session)

        return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        password_valid = verify_password(password, user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": user.uid,
                    "role": user.role,
                },
                jti=str(uuid.uuid4())
            )
            
            refresh_id = str(uuid.uuid4())
            await add_jti_to_logout(refresh_id, user.email)
            
            response = JSONResponse(
                content={
                    "message": "Login successful",
                    "access_token": access_token,
                    "user": {"email": user.email, "uid": user.uid},
                }
            )

            response.set_cookie(
                key="refresh_id",
                value=refresh_id,
                httponly=True,
                secure=False,
                # secure=True,
                max_age=172800,
            )

            return response

    raise InvalidCredentials()


@auth_router.get("/refresh_token")
async def get_new_access_token(refresh_id: dict = Depends(get_refresh_id_from_cookie), session: AsyncSession = Depends(get_session)):

    user_email = await token_in_logout(refresh_id)

    if not refresh_id or not user_email:
        return JSONResponse(
            content={"detail": "Invalid refresh token !!!"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    user = await user_service.get_user_by_email(user_email, session)
    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": user.uid,
            "role": user.role,
        },
        jti=str(uuid.uuid4())
    )

    await remove_jti_from_logout(refresh_id)
    refresh_id = str(uuid.uuid4())
    await add_jti_to_logout(refresh_id, user.email)

    response = JSONResponse(
                content={
                    "access_token": access_token,
                    "user": {"email": user.email, "uid": user.uid},
                }
            )

    response.set_cookie(
        key="refresh_id",
        value=refresh_id,
        httponly=True,
        secure=False,
        # secure=True,
        max_age=172800,
    )

    return response


@auth_router.get("/me", response_model=UserBooksModel)
async def get_current_user(
    user=Depends(get_current_user), _: bool = Depends(role_checker)
):
    return user


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(access_token_bearer), refresh_id: str = Depends(get_refresh_id_from_cookie)):

    await remove_jti_from_logout(refresh_id)
    await add_jti_to_logout(token_details["jti"], "Invalid", ACCESS_TOKEN_EXPIRY)

    response = JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )

    response.set_cookie(
        key="refresh_id",
        value="",
        httponly=True,
        secure=False,
        # secure=True,
        max_age=0,
    )

    return response


@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: EmailModel, passwords: PasswordResetConfirmModel):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
        )
    
    email = email_data.email

    passwd_hash = generate_passwd_hash(new_password)

    token = create_url_safe_token({"email": email, "passwd_hash": passwd_hash})

    link = f"http://{Config.DOMAIN}:{Config.APP_PORT}/api/{version}/auth/password-reset-confirm/{token}"

    html_message = f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a> to Reset Your Password</p>
    """
    subject = "Reset Your Password"

    send_email.send([email], subject, html_message)

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.get("/password-reset-confirm/{token}", include_in_schema=False)
async def reset_account_password(
    token: str,
    session: AsyncSession = Depends(get_session),
):
    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email", None)
    passwd_hash = token_data.get("passwd_hash", None)

    if user_email and passwd_hash:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"password_hash": passwd_hash}, session)

        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occurred during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )