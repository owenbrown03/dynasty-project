from app.core.config import Settings


def test_cors_origins_parses_comma_separated_values():
    settings = Settings(
        ENVIRONMENT="test",
        DATABASE_URL="postgresql://user:pass@db:5432/test",
        ENCRYPTION_KEY="secret",
        REDIS_URL="redis://redis:6379/0",
        BACKEND_CORS_ORIGINS=(
            "http://localhost:5173, "
            "https://dynastybase.app"
        ),
    )

    assert settings.cors_origins == [
        "http://localhost:5173",
        "https://dynastybase.app",
    ]


def test_async_database_url_normalizes_plain_postgres_url():
    settings = Settings(
        ENVIRONMENT="test",
        DATABASE_URL="postgresql://user:pass@db:5432/test",
        ENCRYPTION_KEY="secret",
        REDIS_URL="redis://redis:6379/0",
    )

    assert settings.async_database_url == (
        "postgresql+asyncpg://user:pass@db:5432/test"
    )


def test_async_database_url_preserves_existing_async_driver():
    settings = Settings(
        ENVIRONMENT="test",
        DATABASE_URL=(
            "postgresql+asyncpg://user:pass@db:5432/test"
        ),
        ENCRYPTION_KEY="secret",
        REDIS_URL="redis://redis:6379/0",
    )

    assert settings.async_database_url == (
        "postgresql+asyncpg://user:pass@db:5432/test"
    )
