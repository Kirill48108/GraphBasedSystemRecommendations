from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_user_from_db,
    verify_password,
)
from app.models.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=Token,
    summary="Получить JWT-токен по логину/паролю (OAuth2 password flow)",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Аутентификация пользователя и выдача JWT-токена.

    Ожидает body в формате x-www-form-urlencoded:
      username=<имя>&password=<пароль>
    """
    user = get_user_from_db(form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token, expires_at = create_access_token(
        data={"sub": user.user_id, "role": user.role},
        expires_delta=access_token_expires,
    )

    return Token(access_token=token, expires_at=expires_at)
