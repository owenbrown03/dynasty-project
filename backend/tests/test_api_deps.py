import pytest
from fastapi import HTTPException

from app.api.deps import require_sleeper_connection


class DummyContext:
    def __init__(self, connection):
        self.connection = connection


def test_require_sleeper_connection_allows_connected_context():
    require_sleeper_connection(
        DummyContext(connection=object()),
        detail="unused",
    )


def test_require_sleeper_connection_rejects_missing_connection():
    with pytest.raises(HTTPException) as exc_info:
        require_sleeper_connection(
            DummyContext(connection=None),
            detail="Connect first.",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Connect first."
