from typing import Any, Dict, Optional
from celery.result import AsyncResult
from app.workers.tasks import (
    send_email_task,
    resize_image_task,
    process_data_task,
    generate_report_task,
)


class QueueService:
    @staticmethod
    def submit_job(job_type: str, payload: Dict[str, Any]) -> str:
        """
        Dispatches the requested job type to the respective Celery task.
        Returns the unique task UUID string.
        """
        if job_type == "send_email":
            # Extract email payload fields
            email = payload.get("email")
            subject = payload.get("subject", "Notification")
            body = payload.get("body", "")
            task = send_email_task.delay(email=email, subject=subject, body=body)

        elif job_type == "resize_image":
            image_url = payload.get("image_url", "http://example.com/original.jpg")
            width = payload.get("width", 800)
            height = payload.get("height", 600)
            task = resize_image_task.delay(image_url=image_url, width=width, height=height)

        elif job_type == "process_data":
            dataset_size = payload.get("dataset_size", 1000)
            task = process_data_task.delay(dataset_size=dataset_size)

        elif job_type == "generate_report":
            report_id = payload.get("report_id", "REP-1234")
            file_format = payload.get("format", "PDF")
            task = generate_report_task.delay(report_id=report_id, format=file_format)

        else:
            raise ValueError(f"Unsupported job_type: {job_type}")

        return task.id

    @staticmethod
    def get_job_status(job_id: str) -> Dict[str, Any]:
        """
        Queries the Celery Result Backend to inspect task status and custom progress metadata.
        Maps internal Celery states to user-friendly states (queued, processing, completed, failed).
        """
        res = AsyncResult(job_id)
        state = res.state

        # Map to customer-specified states: queued, processing, completed, failed
        status = "queued"
        progress = 0
        result = None

        if state == "PENDING":
            status = "queued"
            progress = 0
        elif state == "STARTED":
            status = "processing"
            progress = 0
        elif state == "PROCESSING":
            status = "processing"
            # In Celery, custom intermediate states write dictionary info to info/result
            if isinstance(res.info, dict):
                progress = res.info.get("progress", 0)
            else:
                progress = 25
        elif state == "SUCCESS":
            status = "completed"
            progress = 100
            result = res.result
        elif state == "FAILURE":
            status = "failed"
            progress = 0
            # If failed, res.result will contain the exception string
            result = {"error": str(res.result)}
        elif state in ("REVOKED", "RETRY"):
            status = "failed"
            progress = 0
            result = {"error": f"Task state: {state}"}

        return {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "result": result,
        }

    @staticmethod
    def get_job_result(job_id: str) -> Optional[Any]:
        """
        Fetches the final return payload of the job once it is successful.
        """
        res = AsyncResult(job_id)
        if res.state == "SUCCESS":
            return res.result
        return None
