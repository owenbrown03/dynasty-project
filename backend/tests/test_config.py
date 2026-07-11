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
