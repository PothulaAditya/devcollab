from app.models.models import User
from app.utils.utils import hash_password


def test_login_unverified_user(create_test_user, client):
    """Test that unverified users cannot log in."""
    create_test_user()
    response = client.post("/login/", data={
        "username": "test@example.com",
        "password": "TestPass1!",
    })
    assert response.status_code == 403
    assert "verify your email" in response.json()["detail"].lower()


def test_login_wrong_password(create_test_user, client, db_session):
    """Test that wrong password returns 401."""
    create_test_user()
    # Verify the user first
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.is_verified = True
    db_session.commit()

    response = client.post("/login/", data={
        "username": "test@example.com",
        "password": "WrongPass1!",
    })
    assert response.status_code == 401


def test_login_success(create_test_user, client, db_session):
    """Test successful login returns tokens."""
    create_test_user()
    # Verify the user first
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.is_verified = True
    db_session.commit()

    response = client.post("/login/", data={
        "username": "test@example.com",
        "password": "TestPass1!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_nonexistent_user(client):
    """Test login with non-existent email returns 401."""
    response = client.post("/login/", data={
        "username": "nobody@example.com",
        "password": "TestPass1!",
    })
    assert response.status_code == 401
