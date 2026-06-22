"""Test that GET /risk now automatically runs a scan! Isolated test database!"""
import sys
from pathlib import Path
import json

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Setup isolated test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def print_curl(method, url, body=None):
    print(f"\n$ curl -X {method} {url}")
    if body:
        print(f"  -H 'Content-Type: application/json' -d '{json.dumps(body)}'")


def print_response(response):
    print(f"\n{response.status_code} {response.reason_phrase}")
    print(json.dumps(response.json(), indent=2))


def main():
    print("=== Testing GET /risk automatic scan ===")
    Base.metadata.create_all(bind=engine)

    # Upload assets
    print("\n--- Step 1: Upload assets ---")
    upload_body = {
        "assets": [
            {"name": "DB01", "asset_type": "database", "criticality": "Critical"},
            {"name": "FW01", "asset_type": "firewall", "criticality": "High"},
        ]
    }
    print_curl("POST", "http://localhost:8000/upload-assets", upload_body)
    response = client.post("/upload-assets", json=upload_body)
    print_response(response)
    db01_id = response.json()["asset_ids"][0]

    # Simulate brute-force
    print("\n--- Step 2: Simulate brute-force ---")
    print_curl("POST", "http://localhost:8000/simulate/bruteforce", {"asset_id": db01_id})
    response = client.post("/simulate/bruteforce", json={"asset_id": db01_id})
    print_response(response)

    # Run detection
    print("\n--- Step 3: Run detection ---")
    print_curl("POST", "http://localhost:8000/detect/run-now")
    response = client.post("/detect/run-now")
    print_response(response)

    # Get ML anomalies
    print("\n--- Step 4: GET /ml/anomalies ---")
    print_curl("GET", "http://localhost:8000/ml/anomalies")
    response = client.get("/ml/anomalies")
    print_response(response)

    # Get risk (this should auto-scan now!)
    print("\n--- Step 5: GET /risk (NO separate scan!) ---")
    print_curl("GET", "http://localhost:8000/risk")
    response = client.get("/risk")
    print_response(response)
    assert response.json()["asset_count"] > 0, "Risk should have assets now!"
    print("\n[OK] GET /risk now automatically runs a scan!")


if __name__ == "__main__":
    main()
