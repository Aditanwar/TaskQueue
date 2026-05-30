# TaskQueue — Distributed Background Job Processing System

TaskQueue is a production-grade, portfolio-ready asynchronous processing platform built with **FastAPI**, **Celery**, and **Redis**. It demonstrates how enterprise-level applications offload long-running computing workloads—such as image scaling, analytical aggregations, bulk communication engines, and PDF report creation—away from client-facing HTTP threads into resilient, distributed worker nodes.

---

## 🏗️ System Architecture

```
                                +-----------------------------+
                                |      Client / Browser       |
                                +-----------------------------+
                                           │       ▲
                        POST /api/jobs     │       │   GET /api/jobs/{id}
                        (payload details)  ▼       │   (polling status)
                                +-----------------------------+
                                |         FastAPI API         |
                                +-----------------------------+
                                           │
                                           │  Dispatches task (.delay())
                                           ▼
                                +-----------------------------+
                                |  Message Broker (Redis DB0) |
                                +-----------------------------+
                                           │
                                           │  Pops serialized task signature
                                           ▼
                                +-----------------------------+
                                |   Celery Worker Process     |
                                +-----------------------------+
                                           │
                                           │  Simulates heavy workloads
                                           │  Periodically updates progress %
                                           ▼
                                +-----------------------------+
                                |    Result Backend (Redis)   |
                                +-----------------------------+
```

---

## 🚀 Key Features

1. **Interactive SaaS Single-Page Dashboard:**
   - **Product Portal:** Sleek dark-mode landing view featuring glassmorphic designs, spotlights, and floating queue cards.
   - **Cockpit Console:** Real-time stats widgets (success ratios, active threads) accompanied by dynamic SVG gauges, interactive forms, and a live monospaced logs console.
   - **Queue Audit Manager:** Complete list of all historical tasks with details dropdowns mapping JSON payloads and outputs.
2. **Four Simulated Workloads:**
   - `send_email`: Simulates SMTP handshakes and email packet dispatches.
   - `resize_image`: Simulates downloading buffers and downscaling dimensions.
   - `process_data`: Ingests numbers, runs aggregations, standard deviation, and outputs analytics.
   - `generate_report`: Queries virtual tables and compiles PDF binary metadata.
3. **Lightweight Raw Redis Alternative:**
   - Fully functional secondary example using direct `LPUSH` and `BLPOP` atomic lists to demonstrate zero-dependency polling-free subscription workers.
4. **Complete Unit Test Coverage:**
   - Comprehensive test suite with mocked Celery state engines achieving **80%+ code coverage**.

---

## 📂 Core Concepts: Celery Distributed Pipelines

* **Task:** A decorated Python function (`@app.task`) outlining the computational workload. Tasks are serialized (typically to JSON) along with their calling arguments when dispatched.
* **Message Broker:** The intermediary transportation layer (Redis or RabbitMQ). It acts as a temporary buffer storing serialized task signatures in high-throughput FIFO structures until a worker is ready to consume them.
* **Worker:** The computational workhorse. A standalone daemon process running outside the web server boundary. It subscribes to the broker, consumes tasks, and executes Python code.
* **Result Backend:** The persistent ledger (Redis). It tracks active task lifecycles (queued, processing, completed, failed), manages execution progress percentages, and holds returned payloads.

---

## ⚙️ Quick Start: Docker Compose (Recommended)

Booting the entire distributed ecosystem requires only a single terminal command.

### 1. Prerequisites
Ensure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed.

### 2. Startup
Clone the repository and run:
```bash
docker compose up --build
```
This single command builds the custom Python container and launches:
1. **FastAPI Web API & Dashboard:** running at [http://localhost:8000](http://localhost:8000)
2. **Redis Message Broker:** running at `localhost:6379`
3. **Celery Worker:** running in a separate, dedicated container
4. **Flower Monitoring Dashboard:** running at [http://localhost:5555](http://localhost:5555)

---

## 🛠️ Local Development Setup

If you prefer to run services manually on your local system:

### 1. Requirements
Ensure you have **Python 3.12+** and a running **Redis** server on port `6379`.

### 2. Installation
Create and activate a virtual environment, then install dependencies:
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run FastAPI Application
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Run Celery Workers
In a new terminal window (with virtual environment active):
```bash
celery -A app.workers.tasks.celery_app worker --loglevel=info
```

### 5. Run Flower Telemetry Dashboard
In a new terminal window:
```bash
celery -A app.workers.tasks.celery_app flower --port=5555
```

---

## 📊 API Examples (cURL)

### 1. Ingest a Background Job
```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "send_email",
    "payload": {
      "email": "reviewer@company.com",
      "subject": "System Verification",
      "body": "Your distributed pipeline compiled this email."
    }
  }'
```
**Response:**
```json
{
  "job_id": "7ca64731-90a8-48b4-a212-be00bc4c69db",
  "status": "queued"
}
```

### 2. Poll Job Status & Progress
```bash
curl -X GET http://localhost:8000/api/jobs/7ca64731-90a8-48b4-a212-be00bc4c69db
```
**Response (During processing):**
```json
{
  "job_id": "7ca64731-90a8-48b4-a212-be00bc4c69db",
  "status": "processing",
  "progress": 60,
  "result": null
}
```

### 3. Fetch Final Returned Result
```bash
curl -X GET http://localhost:8000/api/jobs/7ca64731-90a8-48b4-a212-be00bc4c69db/result
```
**Response (Completed):**
```json
{
  "job_id": "7ca64731-90a8-48b4-a212-be00bc4c69db",
  "result": {
    "recipient": "reviewer@company.com",
    "subject": "System Verification",
    "message_id": "msg-887413@smtp.taskqueue.io",
    "timestamp": "Sat May 30 11:22:15 2026",
    "status": "delivered"
  }
}
```

---

## 🧪 Verification & Unit Testing

To execute the test suite and verify standard coverage ratios:
```bash
# Set PYTHONPATH to ensure Python finds the 'app' module
$env:PYTHONPATH="."  # On Windows PowerShell
export PYTHONPATH="." # On Linux/macOS

pytest --cov=app --cov-report=term-missing tests/
```
