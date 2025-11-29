from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.auth import TokenData, UserInDB
from app.services.arango import arango_service

# Для OAuth2 password flow (используется в /api/v1/auth/token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Контекст хэширования паролей.
# Используем pbkdf2_sha256 — без ограничений 72 байта и без проблем с bcrypt backend.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля пользователя.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Хэширование пароля пользователя.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    """
    Создать JWT-токен.

    :param data: словарь с payload (минимум sub=user_id, role=...)
    :param expires_delta: через сколько истечёт токен
    :return: (token, expires_at)
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, expire


def get_user_from_db(username: str) -> Optional[UserInDB]:
    """
    Получить пользователя по username из коллекции auth_users в ArangoDB.
    """
    db = arango_service.get_db()
    if not db.has_collection("auth_users"):
        return None
    col = db.collection("auth_users")
    cursor = col.find({"username": username}, limit=1)
    docs_iter = cast(Iterable[dict[str, Any]], cursor)
    docs = list(docs_iter)
    if not docs:
        return None
    doc = docs[0]
    return UserInDB(
        user_id=doc["_key"],
        username=doc["username"],
        hashed_password=doc["hashed_password"],
        role=doc.get("role", "user"),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Достать текущего пользователя из JWT-токена.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен доступа",
                headers={"WWW-Authenticate": "Bearer"},
            )
        _ = TokenData(user_id=user_id, role=role)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен доступа",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    db = arango_service.get_db()
    if not db.has_collection("auth_users"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен доступа",
            headers={"WWW-Authenticate": "Bearer"},
        )

    col = db.collection("auth_users")
    raw_doc = col.get(user_id)
    doc = cast(Optional[dict[str, Any]], raw_doc)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен доступа",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserInDB(
        user_id=doc["_key"],
        username=doc["username"],
        hashed_password=doc["hashed_password"],
        role=doc.get("role", "user"),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


async def get_current_admin(user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Зависимость для эндпоинтов, доступных только администратору.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return user
