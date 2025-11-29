import sys

from app.services.arango import arango_service


def main() -> None:
    try:
        arango_service.init_schema()
    except Exception as exc:
        print(f"[init_arango] Ошибка инициализации схемы: {exc}", file=sys.stderr)
        sys.exit(1)

    print("[init_arango] Схема ArangoDB успешно инициализирована.")


if __name__ == "__main__":
    main()
