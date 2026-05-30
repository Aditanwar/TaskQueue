import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """
    Returns a FastAPI TestClient instance.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def mock_celery_delay(monkeypatch):
    """
    Automatically mock all Celery '.delay()' calls in test suites to prevent network calls to Redis.
    """
    mock_task = MagicMock()
    mock_task.id = "mock-uuid-1234-5678"
    
    # Mock each task.delay method
    monkeypatch.setattr("app.workers.tasks.send_email_task.delay", MagicMock(return_value=mock_task))
    monkeypatch.setattr("app.workers.tasks.resize_image_task.delay", MagicMock(return_value=mock_task))
    monkeypatch.setattr("app.workers.tasks.process_data_task.delay", MagicMock(return_value=mock_task))
    monkeypatch.setattr("app.workers.tasks.generate_report_task.delay", MagicMock(return_value=mock_task))
    
    return mock_task
