from unittest.mock import MagicMock
from app.workers.tasks import (
    send_email_task,
    resize_image_task,
    process_data_task,
    generate_report_task,
)


def test_send_email_task_execution():
    """
    Test direct execution of send_email_task.
    """
    # Mock update_state on the bound task itself
    send_email_task.update_state = MagicMock()
    
    result = send_email_task.run(
        email="test@example.com", 
        subject="Integration Test", 
        body="Verification message."
    )
    
    assert result["recipient"] == "test@example.com"
    assert result["status"] == "delivered"
    assert "message_id" in result
    
    # Assert update_state was called for progress updates
    assert send_email_task.update_state.called
    assert send_email_task.update_state.call_count == 3


def test_resize_image_task_execution():
    """
    Test direct execution of resize_image_task.
    """
    resize_image_task.update_state = MagicMock()
    
    result = resize_image_task.run(
        image_url="https://example.com/gallery/landscape.jpg",
        width=400,
        height=300
    )
    
    assert result["original_url"] == "https://example.com/gallery/landscape.jpg"
    assert result["output_dimensions"] == "400x300"
    assert "thumbnail_url" in result
    
    assert resize_image_task.update_state.called


def test_process_data_task_execution():
    """
    Test direct execution of process_data_task.
    """
    process_data_task.update_state = MagicMock()
    
    result = process_data_task.run(dataset_size=100)
    
    assert result["records_ingested"] == 100
    assert "average_score" in result
    assert "category_distributions" in result
    
    assert process_data_task.update_state.called


def test_generate_report_task_execution():
    """
    Test direct execution of generate_report_task.
    """
    generate_report_task.update_state = MagicMock()
    
    result = generate_report_task.run(
        report_id="REP-9988-ABC",
        format="csv"
    )
    
    assert result["report_id"] == "REP-9988-ABC"
    assert result["format"] == "CSV"
    assert "download_url" in result
    
    assert generate_report_task.update_state.called
