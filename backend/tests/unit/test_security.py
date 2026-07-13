import uuid

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_hash_is_salted():
    # Same password, hashed twice, should never produce the same hash —
    # otherwise two users with the same password would be trivially
    # linkable from the stored hash alone.
    assert hash_password("same-password") != hash_password("same-password")


def test_fernet_roundtrip():
    ciphertext = encrypt_secret("super-secret-db-password")
    assert ciphertext != "super-secret-db-password"
    assert decrypt_secret(ciphertext) == "super-secret-db-password"


def test_fernet_rejects_tampered_ciphertext():
    with pytest.raises(ValueError):
        decrypt_secret("not-a-real-fernet-token")


def test_access_and_refresh_tokens_round_trip():
    user_id = uuid.uuid4()
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)

    assert access_payload["sub"] == str(user_id)
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"


def test_decode_rejects_garbage_token():
    with pytest.raises(ValueError):
        decode_token("not-a-jwt")
