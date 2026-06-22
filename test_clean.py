"""Clean test script using FastAPI TestClient!"""
import sys
from pathlib import Path
# Add backend directory to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Create in-memory SQLite database for testing
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


def test_clean_scenario():
    # Create tables
    Base.metadata.create_all(bind=engine)

    print("\n=== Step 1: Upload real assets ===")
    response = client.post(
        "/upload-assets",
        json={
            "assets": [
                {"name": "DB01", "asset_type": "database", "ip_address": "10.0.1.10", "criticality": "Critical"},
                {"name": "FW01", "asset_type": "firewall", "ip_address": "10.0.0.1", "criticality": "High"},
                {"name": "WS01", "asset_type": "workstation", "ip_address": "192.168.1.50", "criticality": "Low"},
            ]
        },
    )
    assert response.status_code == 200
    asset_ids = response.json()["asset_ids"]
    print(f"Uploaded assets: {asset_ids}")

    print("\n=== Step 2: Get /assets ===")
    response = client.get("/assets")
    assert response.status_code == 200
    assets = response.json()
    for a in assets:
        print(f"- {a['asset_id']}: {a['name']} ({a['criticality']})")

    print("\n=== Step 3: Inject brute-force on DB01 ===")
    response = client.post("/simulate/bruteforce", json={"asset_id": asset_ids[0], "intensity": 65})
    assert response.status_code == 200
    print("Injected brute-force attack")

    print("\n=== Step 4: Inject exfiltration + ransomware on FW01 ===")
    client.post("/simulate/exfiltration", json={"asset_id": asset_ids[1]})
    client.post("/simulate/ransomware", json={"asset_id": asset_ids[1]})
    print("Injected attacks on FW01")

    print("\n=== Step 5: Run detection scan ===")
    response = client.post("/detect/run-now")
    assert response.status_code == 200
    detect_result = response.json()
    print(f"Detection result: {detect_result}")

    print("\n=== Step 6: Get /incidents ===")
    response = client.get("/incidents")
    assert response.status_code == 200
    incidents = response.json()
    for inc in incidents:
        print(f"- {inc['incident_id']}: {inc['title']} (severity {inc['severity']}, asset {inc['related_asset_id']})")

    print("\n=== Step 7: Run risk scan ===")
    response = client.post("/risk/scan")
    assert response.status_code == 200
    print("Risk scan completed")

    print("\n=== Step 8: Get /risk ===")
    response = client.get("/risk")
    assert response.status_code == 200
    risk_data = response.json()
    print(f"Total assets in /risk: {risk_data['asset_count']}")
    for asset_risk in risk_data["assets"]:
        print(f"\n- {asset_risk['asset_name']} ({asset_risk['asset_criticality']}):")
        print(f"  - Rule score: {asset_risk['rule_score']}")
        print(f"  - ML score: {asset_risk['ml_score']:.1f}")
        print(f"  - Total score: {asset_risk['total_score']:.1f}")
        print(f"  - Severity: {asset_risk['severity']}")

    # Verify that DB01 and FW01 have correct rule scores!
    db01_risk = next(a for a in risk_data["assets"] if a["asset_name"] == "DB01")
    assert db01_risk["rule_score"] == 30, f"Expected rule score 30 for DB01, got {db01_risk['rule_score']}"
    fw01_risk = next(a for a in risk_data["assets"] if a["asset_name"] == "FW01")
    assert fw01_risk["rule_score"] == 40, f"Expected rule score 40 for FW01, got {fw01_risk['rule_score']}"
    ws01_risk = next(a for a in risk_data["assets"] if a["asset_name"] == "WS01")
    assert ws01_risk["rule_score"] == 0, f"Expected rule score 0 for WS01, got {ws01_risk['rule_score']}"

    print("\n✅ All tests passed! The code is working correctly!")


if __name__ == "__main__":
    test_clean_scenario()
