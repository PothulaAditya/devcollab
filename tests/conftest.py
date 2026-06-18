import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.main import app
from app.celery_worker import celery_app

# Run celery tasks synchronously in tests without broker connection
celery_app.conf.task_always_eager = True

# Use SQLite for testing
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Disable rate limiting for testing
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
        
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()
    
    # Re-enable rate limiting after test
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = True


@pytest.fixture
def create_test_user(client):
    """Helper to create a test user and return the response."""
    def _create_user(
        username="testuser",
        email="test@example.com",
        password="TestPass1!",
    ):
        return client.post("/user/", json={
            "username": username,
            "email": email,
            "password": password,
        })
    return _create_user


@pytest.fixture(autouse=True)
def mock_celery_tasks(monkeypatch):
    """Mock Celery send_email delay function to bypass external SMTP/API calls."""
    from app.celery_worker import send_email
    monkeypatch.setattr(send_email, "delay", lambda *args, **kwargs: None)


@pytest.fixture(autouse=True)
def mock_redis_client(monkeypatch):
    """Mock Redis client methods to prevent connection errors during tests."""
    from app.redis_client import redis_client
    monkeypatch.setattr(redis_client, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(redis_client, "set", lambda *args, **kwargs: True)
    monkeypatch.setattr(redis_client, "delete", lambda *args, **kwargs: 1)
