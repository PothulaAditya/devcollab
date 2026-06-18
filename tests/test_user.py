def test_register_user(create_test_user):
    """Test successful user registration."""
    response = create_test_user()
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "Member"
    assert data["is_verified"] is False
    # Ensure no password hash in response
    assert "password" not in data


def test_register_duplicate_email(create_test_user):
    """Test that duplicate email returns 409."""
    create_test_user()
    response = create_test_user(username="different", email="test@example.com")
    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]


def test_register_duplicate_username(create_test_user):
    """Test that duplicate username returns 409."""
    create_test_user()
    response = create_test_user(username="testuser", email="other@example.com")
    assert response.status_code == 409
    assert "Username already taken" in response.json()["detail"]


def test_register_weak_password(client):
    """Test that weak passwords are rejected."""
    # Too short
    response = client.post("/user/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Ab1!",
    })
    assert response.status_code == 422

    # No uppercase
    response = client.post("/user/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "abcdefg1!",
    })
    assert response.status_code == 422

    # No digit
    response = client.post("/user/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Abcdefgh!",
    })
    assert response.status_code == 422

    # No special char
    response = client.post("/user/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Abcdefgh1",
    })
    assert response.status_code == 422


def test_get_user_not_found(client):
    """Test getting a non-existent user returns 404."""
    response = client.get("/user/9999")
    assert response.status_code == 404


def test_no_password_in_user_response(create_test_user, client):
    """Verify password hash is never exposed in any user endpoint."""
    create_test_user()
    response = client.get("/user/1")
    data = response.json()
    assert "password" not in data
