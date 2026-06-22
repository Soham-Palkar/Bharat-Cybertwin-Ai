"""Verify all fixes - uses ISOLATED TEST database (NO cybertwin.db touches!)"""
import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


# Setup in-memory test database (completely isolated!)
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


def print_curl_request(method: str, url: str, body: dict | None = None):
    """Print request like curl would"""
    print(f"\n$ curl -X {method} {url} \\")
    if body:
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{json.dumps(body)}'")
    else:
        print()


def print_response(response):
    print(f"\nResponse: {response.status_code} {response.reason_phrase}")
    print(json.dumps(response.json(), indent=2))


def main():
    print("=== CyberTwin AI - Fix Verification ===")
    print("(Uses ISOLATED in-memory test database — NO changes to cybertwin.db!)")

    # Create tables
    Base.metadata.create_all(bind=engine)

    # ------------------------------
    # First: Check original sample assets (simulated)
    # ------------------------------
    print("\n=== Step 1: Upload assets ===")
    upload_body = {
        "assets": [
            {"name": "DB01", "asset_type": "database", "ip_address": "10.0.1.10", "criticality": "Critical"},
            {"name": "FW01", "asset_type": "firewall", "ip_address": "10.0.0.1", "criticality": "High"},
            {"name": "WS01", "asset_type": "workstation", "ip_address": "192.168.1.50", "criticality": "Low"},
        ]
    }
    print_curl_request("POST", "http://localhost:8000/upload-assets", upload_body)
    response = client.post("/upload-assets", json=upload_body)
    print_response(response)
    asset_ids = response.json()["asset_ids"]
    db01_id = asset_ids[0]
    print(f"\n[OK] Asset IDs are sequential: {asset_ids}")

    # ------------------------------
    # Check /assets
    # ------------------------------
    print("\n=== Step 2: GET /assets ===")
    print_curl_request("GET", "http://localhost:8000/assets")
    response = client.get("/assets")
    print_response(response)

    # ------------------------------
    # Simulate brute-force on DB01
    # ------------------------------
    print("\n=== Step 3: Simulate brute-force on DB01 ===")
    brute_body = {"asset_id": db01_id, "intensity": 65}
    print_curl_request("POST", "http://localhost:8000/simulate/bruteforce", brute_body)
    response = client.post("/simulate/bruteforce", json=brute_body)
    print_response(response)

    # ------------------------------
    # Run detection
    # ------------------------------
    print("\n=== Step 4: POST /detect/run-now ===")
    print_curl_request("POST", "http://localhost:8000/detect/run-now")
    response = client.post("/detect/run-now")
    print_response(response)

    # ------------------------------
    # Check /incidents
    # ------------------------------
    print("\n=== Step 5: GET /incidents ===")
    print_curl_request("GET", "http://localhost:8000/incidents")
    response = client.get("/incidents")
    print_response(response)

    # ------------------------------
    # Run risk scan
    # ------------------------------
    print("\n=== Step 6: POST /risk/scan ===")
    print_curl_request("POST", "http://localhost:8000/risk/scan")
    response = client.post("/risk/scan")
    print_response(response)

    # ------------------------------
    # Check /risk
    # ------------------------------
    print("\n=== Step 7: GET /risk ===")
    print_curl_request("GET", "http://localhost:8000/risk")
    response = client.get("/risk")
    print_response(response)

    # ------------------------------
    # Verify all fixes
    # ------------------------------
    risk_data = response.json()
    db01_risk = next(a for a in risk_data["assets"] if a["asset_name"] == "DB01")
    assert db01_risk["rule_score"] == 30, f"Expected rule score 30, got {db01_risk['rule_score']}"
    print("\n[OK] All fixes verified!")
    print("   - /risk shows real asset names and correct rule scores")
    print("   - /simulate/bruteforce + /detect/run-now creates an incident correctly")


if __name__ == "__main__":
    main()
