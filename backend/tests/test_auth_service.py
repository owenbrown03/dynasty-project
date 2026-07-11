from app.services.auth import build_auth_session_response


def test_build_auth_session_response_for_authenticated_user():
    response = build_auth_session_response(
        "user-123",
    )

    assert response.authenticated is True
    assert response.user_id == "user-123"


def test_build_auth_session_response_for_anonymous_user():
    response = build_auth_session_response(
        None,
    )

    assert response.authenticated is False
    assert response.user_id is None
