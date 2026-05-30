import time
import random
from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Optional configuration overrides
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, name="app.workers.tasks.send_email_task")
def send_email_task(self, email: str, subject: str = "Notification", body: str = ""):
    """
    Simulates sending an email with validation and SMTP delays.
    """
    print(f"[CELERY] Starting send_email_task to {email}")
    
    # 10% - Validation
    self.update_state(state="PROCESSING", meta={"progress": 10, "step": "Validating recipient"})
    time.sleep(1.0)

    # 30% - SMTP Connection
    self.update_state(state="PROCESSING", meta={"progress": 30, "step": "Establishing SMTP Connection"})
    time.sleep(1.2)

    # 60% - Handshake and Sending
    self.update_state(state="PROCESSING", meta={"progress": 60, "step": "Transmitting payload stream"})
    time.sleep(1.5)

    # 100% - Finished
    return {
        "recipient": email,
        "subject": subject,
        "message_id": f"msg-{random.randint(100000, 999999)}@smtp.taskqueue.io",
        "timestamp": time.ctime(),
        "status": "delivered"
    }


@celery_app.task(bind=True, name="app.workers.tasks.resize_image_task")
def resize_image_task(self, image_url: str = "http://example.com/original.jpg", width: int = 800, height: int = 600):
    """
    Simulates downloading, loading, and resizing an image.
    """
    print(f"[CELERY] Starting resize_image_task for {image_url}")
    
    # 10% - Downloading
    self.update_state(state="PROCESSING", meta={"progress": 10, "step": f"Downloading resource: {image_url}"})
    time.sleep(0.8)

    # 30% - Loading buffer
    self.update_state(state="PROCESSING", meta={"progress": 30, "step": "Parsing image dimensions into buffer"})
    time.sleep(1.0)

    # 60% - Downscaling process
    self.update_state(state="PROCESSING", meta={"progress": 60, "step": f"Downscaling interpolation to {width}x{height}"})
    time.sleep(1.4)

    # 100% - Done
    return {
        "original_url": image_url,
        "output_dimensions": f"{width}x{height}",
        "file_size_bytes": random.randint(15000, 45000),
        "thumbnail_url": f"https://s3.amazonaws.com/taskqueue-buckets/thumbs/thumb_{random.randint(1000, 9999)}.jpg",
        "processed_at": time.ctime()
    }


@celery_app.task(bind=True, name="app.workers.tasks.process_data_task")
def process_data_task(self, dataset_size: int = 1000):
    """
    Generates large mock datasets, performs filtering, aggregation and calculates averages.
    """
    print(f"[CELERY] Starting process_data_task with size {dataset_size}")
    
    # 10% - Generates large mock list
    self.update_state(state="PROCESSING", meta={"progress": 10, "step": f"Generating mock dataset of {dataset_size} entries"})
    time.sleep(1.0)
    raw_data = [{"id": i, "score": random.uniform(10, 100), "category": random.choice(["A", "B", "C", "D"])} for i in range(dataset_size)]

    # 30% - Filtering
    self.update_state(state="PROCESSING", meta={"progress": 30, "step": "Filtering outliers (scores < 20)"})
    time.sleep(1.2)
    filtered = [x for x in raw_data if x["score"] >= 20.0]

    # 60% - Analysis/Aggregations
    self.update_state(state="PROCESSING", meta={"progress": 60, "step": "Aggregating metrics, standard deviation, and categories"})
    time.sleep(1.5)
    
    category_counts = {}
    total_score = 0.0
    for x in filtered:
        cat = x["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_score += x["score"]
    
    average_score = total_score / len(filtered) if filtered else 0.0

    # 100% - Finish
    return {
        "records_ingested": dataset_size,
        "records_processed": len(filtered),
        "average_score": round(average_score, 2),
        "category_distributions": category_counts,
        "execution_duration_sec": 3.7
    }


@celery_app.task(bind=True, name="app.workers.tasks.generate_report_task")
def generate_report_task(self, report_id: str, format: str = "PDF"):
    """
    Simulates database record collection and compilation into formatted PDF binary meta-info.
    """
    print(f"[CELERY] Starting generate_report_task for {report_id}")
    
    # 10% - Loading records
    self.update_state(state="PROCESSING", meta={"progress": 10, "step": "Querying analytical records from primary tables"})
    time.sleep(1.0)

    # 30% - Parsing templates
    self.update_state(state="PROCESSING", meta={"progress": 30, "step": f"Populating elements into report templates ({format})"})
    time.sleep(1.0)

    # 60% - PDF Compilations
    self.update_state(state="PROCESSING", meta={"progress": 60, "step": f"Compiling styles, vector graphics, and tables into final {format}"})
    time.sleep(1.5)

    # 100% - Finished
    return {
        "report_id": report_id,
        "format": format.upper(),
        "total_pages": random.randint(3, 15),
        "report_size_kb": random.randint(350, 1200),
        "download_url": f"https://s3.amazonaws.com/taskqueue-buckets/reports/{report_id}.{format.lower()}",
        "generated_at": time.ctime()
    }
