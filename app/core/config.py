from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Глобальные настройки приложения.
    Все чувствительные значения (пароли, ключи) должны приходить из .env / переменных окружения.
    """

    # Базовые настройки приложения
    app_name: str = "Movie Recommender API"
    app_version: str = "0.1.0"

    # ArangoDB
    # URL сервера ArangoDB. В docker-compose по умолчанию: http://arangodb:8529
    arango_url: str = "http://arangodb:8529"
    # Имя базы данных
    arango_db: str = "movies"
    # Пользователь и пароль БД (в проде ОБЯЗАТЕЛЬНО задать через .env)
    arango_user: str = "root"
    arango_password: str = "password"

    # Redis
    # URL подключения к Redis (в docker-compose: redis://redis:6379/0)
    redis_url: str = "redis://redis:6379/0"

    # Веса для гибридного алгоритма
    hybrid_weight_popular: float = 0.4
    hybrid_weight_cf: float = 0.3
    hybrid_weight_pr: float = 0.3

    # Лимит запросов (rate limiting)
    rate_limit_requests_per_minute: int = 60

    # Безопасность / JWT
    # ВАЖНО: SECRET_KEY нужно переопределить в .env на случайное значение
    secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # A/B
    ab_seed: int = 42
    default_variant: str = "A"

    # Рекомендации
    rec_ttl_hours: int = 1

    # Демо-админ (используется ТОЛЬКО скриптом create_demo_admin)
    demo_admin_username: str = "admin"
    demo_admin_password: str = "admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
