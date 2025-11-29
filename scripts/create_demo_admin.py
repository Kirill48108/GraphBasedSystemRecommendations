import sys

from app.core.config import settings
from app.core.security import hash_password
from app.services.arango import arango_service


def main() -> None:
    username = settings.demo_admin_username
    password = settings.demo_admin_password

    hashed = hash_password(password)
    try:
        user_id = arango_service.create_auth_user(
            username=username,
            hashed_password=hashed,
            role="admin",
        )
    except Exception as exc:
        print(
            f"[create_demo_admin] Ошибка создания пользователя: {exc}", file=sys.stderr
        )
        sys.exit(1)

    print(
        f"[create_demo_admin] Админ-пользователь создан/существует:"
        f" username={username}, user_id={user_id}"
    )


if __name__ == "__main__":
    main()
