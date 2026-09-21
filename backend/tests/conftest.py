import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend and project root are in sys.path
backend_root = Path(__file__).resolve().parent.parent
project_root = backend_root.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# Use in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create test tables before tests run, tear down afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with database dependency overridden."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    from app.services.task_runner import FastAPIBackgroundTaskRunner, get_task_runner

    test_runner = FastAPIBackgroundTaskRunner(session_factory=TestingSessionLocal)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_task_runner] = lambda: test_runner
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
