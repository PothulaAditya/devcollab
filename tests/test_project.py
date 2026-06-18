from app.models.models import User, ProjectMember
from app.Auth.oauth2 import create_token


def get_auth_headers(user_id: int):
    """Helper to create auth headers for a user."""
    token = create_token(data={"user_id": user_id})
    return {"Authorization": f"Bearer {token}"}


def test_create_project(create_test_user, client, db_session):
    """Test project creation and auto-membership of owner."""
    create_test_user()
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.is_verified = True
    db_session.commit()

    headers = get_auth_headers(user.id)
    response = client.post("/project/", json={
        "title": "Test Project",
        "description": "A test project",
        "tech_stack": "Python, FastAPI",
        "required_roles": "Backend Developer",
    }, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["owner_id"] == user.id
    assert "created_at" in data

    # Verify owner was auto-added as project member
    member = db_session.query(ProjectMember).filter(
        ProjectMember.project_id == data["id"],
        ProjectMember.user_id == user.id,
    ).first()
    assert member is not None
    assert member.role == "owner"


def test_list_projects_with_pagination(create_test_user, client, db_session):
    """Test project listing with pagination."""
    create_test_user()
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.is_verified = True
    db_session.commit()

    headers = get_auth_headers(user.id)

    # Create 3 projects
    for i in range(3):
        client.post("/project/", json={
            "title": f"Project {i}",
            "description": f"Description {i}",
            "tech_stack": "Python",
            "required_roles": "Dev",
        }, headers=headers)

    # Get all
    response = client.get("/project/")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Get with limit
    response = client.get("/project/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Get with skip
    response = client.get("/project/?skip=2&limit=10")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_project_not_found(create_test_user, client, db_session):
    """Test getting a non-existent project returns 404."""
    create_test_user()
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.is_verified = True
    db_session.commit()

    headers = get_auth_headers(user.id)
    response = client.get("/project/9999", headers=headers)
    assert response.status_code == 404


def test_partial_project_update(create_test_user, client, db_session):
    """Test that partial update only changes specified fields."""
    create_test_user()
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    user.is_verified = True
    db_session.commit()

    headers = get_auth_headers(user.id)
    # Create project
    create_resp = client.post("/project/", json={
        "title": "Original Title",
        "description": "Original description",
        "tech_stack": "Python",
        "required_roles": "Dev",
    }, headers=headers)
    project_id = create_resp.json()["id"]

    # Partial update — only title
    update_resp = client.put(f"/project/{project_id}", json={
        "title": "Updated Title",
    }, headers=headers)

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Original description"  # Unchanged
