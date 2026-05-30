from unittest.mock import patch
from fastapi.testclient import TestClient


def test_submit_valid_job(client: TestClient):
    """
    Test submitting a valid 'send_email' background job.
    """
    response = client.post(
        "/api/jobs",
        json={
            "job_type": "send_email",
            "payload": {
                "email": "portfolio_reviewer@example.com",
                "subject": "Greetings!",
                "body": "Welcome to my TaskQueue demonstration."
            }
        }
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert data["job_id"] == "mock-uuid-1234-5678"


def test_submit_invalid_job_type(client: TestClient):
    """
    Test submitting a job with an unsupported job_type.
    """
    response = client.post(
        "/api/jobs",
        json={
            "job_type": "mine_bitcoin",
            "payload": {"wallet_address": "0x123"}
        }
    )
    
    assert response.status_code == 422
    assert "detail" in response.json()


def test_submit_malformed_email_payload(client: TestClient):
    """
    Test submitting a 'send_email' job missing the required 'email' field or malformed format.
    """
    # Missing email
    response = client.post(
        "/api/jobs",
        json={
            "job_type": "send_email",
            "payload": {"subject": "No Email Recipient!"}
        }
    )
    assert response.status_code == 422

    # Malformed email (missing '@')
    response2 = client.post(
        "/api/jobs",
        json={
            "job_type": "send_email",
            "payload": {"email": "invalid_email_format"}
        }
    )
    assert response2.status_code == 422


@patch("app.services.queue_service.QueueService.get_job_status")
def test_get_job_status_queued(mock_get_status, client: TestClient):
    """
    Test status endpoint when the task is queued.
    """
    mock_get_status.return_value = {
        "job_id": "test-uuid",
        "status": "queued",
        "progress": 0,
        "result": None
    }
    
    response = client.get("/api/jobs/test-uuid")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["progress"] == 0


@patch("app.services.queue_service.QueueService.get_job_status")
def test_get_job_status_processing(mock_get_status, client: TestClient):
    """
    Test status endpoint when the task is executing and shows intermediate progress.
    """
    mock_get_status.return_value = {
        "job_id": "test-uuid",
        "status": "processing",
        "progress": 60,
        "result": None
    }
    
    response = client.get("/api/jobs/test-uuid")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress"] == 60


@patch("app.services.queue_service.QueueService.get_job_status")
def test_get_job_status_completed(mock_get_status, client: TestClient):
    """
    Test status endpoint when the task has completed and returned results.
    """
    mock_get_status.return_value = {
        "job_id": "test-uuid",
        "status": "completed",
        "progress": 100,
        "result": {"recipient": "user@example.com", "status": "delivered"}
    }
    
    response = client.get("/api/jobs/test-uuid")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["result"]["status"] == "delivered"


@patch("app.services.queue_service.QueueService.get_job_status")
def test_get_job_result_not_ready(mock_get_status, client: TestClient):
    """
    Test fetching the result when the job is still active or queued (should return 202).
    """
    mock_get_status.return_value = {
        "job_id": "test-uuid",
        "status": "processing",
        "progress": 30,
        "result": None
    }
    
    response = client.get("/api/jobs/test-uuid/result")
    assert response.status_code == 202
    assert "still executing" in response.json()["detail"]


@patch("app.services.queue_service.QueueService.get_job_result")
@patch("app.services.queue_service.QueueService.get_job_status")
def test_get_job_result_completed(mock_get_status, mock_get_result, client: TestClient):
    """
    Test fetching the result when the job is completed.
    """
    mock_get_status.return_value = {
        "job_id": "test-uuid",
        "status": "completed",
        "progress": 100,
        "result": {"status": "success"}
    }
    mock_get_result.return_value = {"thumbnail_url": "https://s3/thumb.jpg", "file_size_bytes": 12000}
    
    response = client.get("/api/jobs/test-uuid/result")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-uuid"
    assert data["result"]["file_size_bytes"] == 12000
