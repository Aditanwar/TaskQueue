import json
import time
import sys
import redis

# Redis Configuration
REDIS_URL = "redis://localhost:6379/0"
QUEUE_NAME = "raw_queue:jobs"


def simulate_task_execution(job_id: str, job_type: str, payload: dict, r: redis.Redis):
    """
    Simulates task execution and writes milestones (progress) to Redis status key.
    """
    print(f"\n[WORKER] Starting Job {job_id} ({job_type})...")
    status_key = f"raw_job:{job_id}"

    # Setup initial status in Redis
    r.set(status_key, json.dumps({"status": "processing", "progress": 0, "result": None}))

    # Progress steps
    steps = [10, 30, 60, 100]
    for step in steps:
        time.sleep(1.0)  # Simulate latency
        print(f"[WORKER] Job {job_id} progress: {step}%")
        r.set(status_key, json.dumps({
            "status": "processing" if step < 100 else "completed",
            "progress": step,
            "result": f"Success: processed {job_type} at {time.ctime()}" if step == 100 else None
        }))

    print(f"[WORKER] Job {job_id} completed successfully!")


def start_worker():
    """
    Main blocking consumer loop using BLPOP.
    """
    try:
        r = redis.from_url(REDIS_URL)
        print(f"[WORKER] Connected to Redis. Listening on queue '{QUEUE_NAME}'...")
        print("[WORKER] Waiting for jobs... (Press Ctrl+C to exit)")

        while True:
            # BLPOP is blocking: it suspends the worker thread until a job is pushed.
            # Timeout = 0 means block indefinitely.
            # blpop returns a tuple: (queue_name, popped_value)
            pop_result = r.blpop(QUEUE_NAME, timeout=0)
            
            if not pop_result:
                continue

            _, job_payload_raw = pop_result
            try:
                job_data = json.loads(job_payload_raw)
                job_id = job_data["job_id"]
                job_type = job_data["job_type"]
                payload = job_data["payload"]

                simulate_task_execution(job_id, job_type, payload, r)
            except Exception as ex:
                print(f"[WORKER] Failed to process message: {ex}", file=sys.stderr)

    except redis.ConnectionError as e:
        print(f"[WORKER] Connection failed: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[WORKER] Exiting worker gracefully.")


if __name__ == "__main__":
    start_worker()
