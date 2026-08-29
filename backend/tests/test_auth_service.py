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


def test_pwd_context_supports_argon2_and_pbkdf2():
    from app.services.auth import pwd_context

    # Verify argon2 hashing and verification
    argon2_hash = pwd_context.hash("secret123", scheme="argon2")
    assert "$argon2id$" in argon2_hash
    assert pwd_context.verify("secret123", argon2_hash) is True
    assert pwd_context.verify("wrongpassword", argon2_hash) is False

    # Verify pbkdf2_sha256
    pbkdf2_hash = pwd_context.hash("secret123", scheme="pbkdf2_sha256")
    assert pwd_context.verify("secret123", pbkdf2_hash) is True
    assert pwd_context.verify("wrongpassword", pbkdf2_hash) is False

