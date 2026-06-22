# CyberTwin AI — AI-Powered Cybersecurity Digital Twin & SOC Copilot

This repository contains **Module 1: Asset Discovery** and **Module 2: Log Collection** for the CyberTwin AI SOC Copilot platform.

## Setup Instructions

### 1. Prerequisites
- Python 3.11+

### 2. Create and Activate Virtual Environment
From the project root directory, run:
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

---

## Running the Application

To start the FastAPI development server:
```bash
uvicorn backend.app.main:app --reload
```
Upon startup, the server will:
1. Automatically create/initialize the SQLite database at `backend/cybertwin.db`.
2. Start the synthetic log generator background task (which runs every few seconds if assets are present).

---

## API Documentation & Curl Examples

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 1. Bulk Upload Assets (CSV)
Uploads assets in bulk using the sample CSV file.
```bash
curl -X POST -F "file=@data/sample_assets.csv" http://127.0.0.1:8000/upload-assets
```

### 2. Bulk Upload Assets (JSON)
Uploads assets in bulk using a JSON payload.
```bash
curl -X POST -H "Content-Type: application/json" -d @data/sample_assets.json http://127.0.0.1:8000/upload-assets
```

### 3. Get Assets (Sorted by Criticality)
Lists all assets currently stored in the database, ordered by criticality (Critical > High > Medium > Low).
```bash
curl http://127.0.0.1:8000/assets
```

### 4. Connect to Live WebSocket Log Stream
You can test the real-time websocket endpoint `/ws/logs` using any WebSocket client or using python's `websockets` library.
For example, using a simple Python script to listen to the logs:
```python
import asyncio
import websockets

async def listen():
    uri = "ws://127.0.0.1:8000/ws/logs"
    async with websockets.connect(uri) as websocket:
        print("Connected to CyberTwin live event stream. Waiting for events...")
        while True:
            message = await websocket.recv()
            print(f"New Event: {message}")

asyncio.run(listen())
```

---

## Running the Automated Test Suite

To run the automated tests verifying asset uploads, validation logic, and websocket streaming:
```bash
python -m pytest
```
