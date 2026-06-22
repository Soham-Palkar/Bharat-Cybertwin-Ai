"""Test ml score rescaling! Isolated test db!"""
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
    print("=== Testing ml_score rescaling ===")
    Base.metadata.create_all(bind=engine)

    # Upload assets
    print("\n--- Step 1: Upload 5 assets ---")
    upload_body = {
        "assets": [
            {"name": "DB01", "asset_type": "database", "criticality": "Critical"},
            {"name": "FW01", "asset_type": "firewall", "criticality": "High"},
            {"name": "WS01", "asset_type": "workstation", "criticality": "Low"},
            {"name": "WS02", "asset_type": "workstation", "criticality": "Low"},
            {"name": "WS03", "asset_type": "workstation", "criticality": "Low"},
        ]
    }
    print_curl("POST", "http://localhost:8000/upload-assets", upload_body)
    response = client.post("/upload-assets", json=upload_body)
    print_response(response)
    db01_id = response.json()["asset_ids"][0]

    # Simulate brute-force on DB01
    print("\n--- Step 2: Simulate brute-force on DB01 ---")
    print_curl("POST", "http://localhost:8000/simulate/bruteforce", {"asset_id": db01_id})
    client.post("/simulate/bruteforce", json={"asset_id": db01_id})

    # Run detection
    print("\n--- Step3: /detect/run-now ---")
    client.post("/detect/run-now")

    # Get risk
    print("\n--- Step4: GET /risk ---")
    print_curl("GET", "http://localhost:8000/risk")
    response = client.get("/risk")
    print_response(response)

    # Verify DB01 is first
    assets = response.json()["assets"]
    assert assets[0]["asset_name"] == "DB01", "DB01 should be highest risk!"
    print("\n[OK] DB01 (with real incident) is now highest rank!")


if __name__ == "__main__":
    main()
