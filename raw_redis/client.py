import json
import uuid
import sys
import redis

# Redis Configuration (Must match settings)
REDIS_URL = "redis://localhost:6379/0"
QUEUE_NAME = "raw_queue:jobs"


def submit_job(job_type: str, payload: dict):
    """
    Submits a job to the raw Redis queue using LPUSH.
    """
    try:
        r = redis.from_url(REDIS_URL)
        job_id = str(uuid.uuid4())

        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "payload": payload
        }

        # LPUSH pushes the job payload onto the Left of the list
        r.lpush(QUEUE_NAME, json.dumps(job_data))
        print(f"[PRODUCER] Submitted {job_type} job (ID: {job_id}) successfully.")
        return job_id
    except redis.ConnectionError as e:
        print(f"[PRODUCER] Failed to connect to Redis: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    print("--- Running Raw Redis Queue Client (Producer) ---")
    
    # Submit some sample jobs
    submit_job("send_email", {"email": "portfolio_reviewer@example.com", "subject": "Hello from Raw Redis Queue!"})
    submit_job("resize_image", {"image_url": "http://example.com/hero.png", "width": 800, "height": 600})
    submit_job("process_data", {"dataset_size": 5000})
    submit_job("generate_report", {"report_id": "REP-9988", "format": "PDF"})
    
    print("--- Done submitting. Start raw_redis/worker.py to process them! ---")
