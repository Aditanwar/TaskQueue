import pytest
from unittest.mock import patch, MagicMock
from app.services.queue_service import QueueService


def test_submit_job_types():
    """
    Test that all supported job types dispatch correctly to Celery.
    """
    # Using the auto-mocked celery delays from conftest
    id_email = QueueService.submit_job("send_email", {"email": "test@domain.com"})
    assert id_email == "mock-uuid-1234-5678"

    id_resize = QueueService.submit_job("resize_image", {"image_url": "http://img.png", "width": 100})
    assert id_resize == "mock-uuid-1234-5678"

    id_data = QueueService.submit_job("process_data", {"dataset_size": 250})
    assert id_data == "mock-uuid-1234-5678"

    id_report = QueueService.submit_job("generate_report", {"report_id": "REP-001"})
    assert id_report == "mock-uuid-1234-5678"

    with pytest.raises(ValueError):
        QueueService.submit_job("invalid_job_type", {})


@patch("app.services.queue_service.AsyncResult")
def test_get_job_status_states(mock_async_result):
    """
    Test state mappings inside queue_service.py for all major Celery states.
    """
    # 1. Test PENDING
    mock_res_pending = MagicMock()
    mock_res_pending.state = "PENDING"
    mock_async_result.return_value = mock_res_pending
    
    status_pending = QueueService.get_job_status("uuid-pending")
    assert status_pending["status"] == "queued"
    assert status_pending["progress"] == 0

    # 2. Test STARTED
    mock_res_started = MagicMock()
    mock_res_started.state = "STARTED"
    mock_async_result.return_value = mock_res_started
    
    status_started = QueueService.get_job_status("uuid-started")
    assert status_started["status"] == "processing"
    assert status_started["progress"] == 0

    # 3. Test PROCESSING (with custom dict info)
    mock_res_proc = MagicMock()
    mock_res_proc.state = "PROCESSING"
    mock_res_proc.info = {"progress": 60, "step": "Working"}
    mock_async_result.return_value = mock_res_proc
    
    status_proc = QueueService.get_job_status("uuid-proc")
    assert status_proc["status"] == "processing"
    assert status_proc["progress"] == 60

    # 4. Test PROCESSING (with non-dict info)
    mock_res_proc_raw = MagicMock()
    mock_res_proc_raw.state = "PROCESSING"
    mock_res_proc_raw.info = "Just string"
    mock_async_result.return_value = mock_res_proc_raw
    
    status_proc_raw = QueueService.get_job_status("uuid-proc-raw")
    assert status_proc_raw["status"] == "processing"
    assert status_proc_raw["progress"] == 25

    # 5. Test SUCCESS
    mock_res_success = MagicMock()
    mock_res_success.state = "SUCCESS"
    mock_res_success.result = {"recipient": "ok"}
    mock_async_result.return_value = mock_res_success
    
    status_success = QueueService.get_job_status("uuid-success")
    assert status_success["status"] == "completed"
    assert status_success["progress"] == 100
    assert status_success["result"] == {"recipient": "ok"}

    # 6. Test FAILURE
    mock_res_failure = MagicMock()
    mock_res_failure.state = "FAILURE"
    mock_res_failure.result = Exception("Task crashed")
    mock_async_result.return_value = mock_res_failure
    
    status_failure = QueueService.get_job_status("uuid-failure")
    assert status_failure["status"] == "failed"
    assert status_failure["progress"] == 0
    assert "Task crashed" in status_failure["result"]["error"]


@patch("app.services.queue_service.AsyncResult")
def test_get_job_result_direct(mock_async_result):
    """
    Test direct retrieval of job outputs.
    """
    # Success task
    mock_res_success = MagicMock()
    mock_res_success.state = "SUCCESS"
    mock_res_success.result = {"data": "output_payload"}
    mock_async_result.return_value = mock_res_success
    
    result = QueueService.get_job_result("uuid-success")
    assert result == {"data": "output_payload"}

    # Pending task (should return None)
    mock_res_pending = MagicMock()
    mock_res_pending.state = "PENDING"
    mock_async_result.return_value = mock_res_pending
    
    result_pending = QueueService.get_job_result("uuid-pending")
    assert result_pending is None
