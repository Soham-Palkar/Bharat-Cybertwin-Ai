"""
Tests for Module 5 (ML Anomaly Detection) and Module 6 (Risk Engine)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Asset, Event, Incident
from backend.app.services.feature_extraction import extract_features, _extract_single_asset_features, FEATURE_NAMES
from backend.app.services.ml_engine import run_ml_scan
from backend.app.services.risk_engine import run_risk_scan, _calculate_rule_score, _map_score_to_severity, SEVERITY_TO_RULE_SCORE, CRITICALITY_TO_WEIGHT

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_modules_5_6.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_feature_extraction_single_asset(db_session):
    # Create test asset
    asset = Asset(
        asset_id="TEST-001",
        name="Test Asset",
        asset_type="server",
        ip_address="192.168.1.1",
        criticality="High",
        owner="admin"
    )
    db_session.add(asset)
    db_session.commit()

    # Create test events
    now = datetime.utcnow()
    events = [
        Event(
            event_id=f"EVT-{i}",
            asset_id="TEST-001",
            source_ip="10.0.0.1",
            event_type="login_failed",
            raw_payload="Failed password for user",
            timestamp=now - timedelta(minutes=1)
        ) for i in range(5)
    ]
    events.append(
        Event(
            event_id="EVT-5",
            asset_id="TEST-001",
            source_ip="10.0.0.2",
            event_type="download",
            raw_payload="File downloaded",
            timestamp=now - timedelta(minutes=2)
        )
    )
    events.append(
        Event(
            event_id="EVT-6",
            asset_id="TEST-001",
            source_ip="10.0.0.3",
            event_type="data_transfer",
            raw_payload="Transferred 1000000 bytes",
            timestamp=now - timedelta(minutes=3)
        )
    )
    events.append(
        Event(
            event_id="EVT-7",
            asset_id="TEST-001",
            source_ip="10.0.0.4",
            event_type="admin_action",
            raw_payload="User admin did something",
            timestamp=now - timedelta(minutes=4)
        )
    )

    for e in events:
        db_session.add(e)
    db_session.commit()

    # Test feature extraction
    features = extract_features(db_session)
    assert "TEST-001" in features
    feat = features["TEST-001"]
    assert feat["failed_login_count"] == 5.0
    assert feat["download_count"] == 1.0
    assert feat["bytes_transferred_total"] == 1000000.0
    assert feat["admin_action_count"] == 1.0


def test_ml_scan_runs_without_error(db_session):
    # Create a few assets with events
    asset1 = Asset(asset_id="A1", name="A1", asset_type="server", criticality="Medium")
    asset2 = Asset(asset_id="A2", name="A2", asset_type="endpoint", criticality="Low")
    db_session.add_all([asset1, asset2])
    db_session.commit()

    now = datetime.utcnow()
    for i in range(10):
        db_session.add(Event(
            event_id=f"E-A1-{i}",
            asset_id="A1",
            event_type="login_success",
            timestamp=now - timedelta(minutes=i)
        ))
        db_session.add(Event(
            event_id=f"E-A2-{i}",
            asset_id="A2",
            event_type="login_success",
            timestamp=now - timedelta(minutes=i)
        ))
    db_session.commit()

    # Run ML scan
    ml_scores = run_ml_scan(db_session)
    assert len(ml_scores) == 2
    assert "anomaly_score" in ml_scores["A1"]
    assert "threat_confidence" in ml_scores["A1"]
    assert 0 <= ml_scores["A1"]["threat_confidence"] <= 100


def test_risk_calculation_works(db_session):
    # Create test asset
    asset = Asset(
        asset_id="RISK-001",
        name="Risk Test Asset",
        asset_type="server",
        criticality="Critical"  # weight 20
    )
    db_session.add(asset)
    db_session.commit()

    # Create an open High-severity incident
    inc = Incident(
        incident_id="INC-RISK-001",
        title="Test Incident",
        description="Test",
        severity="High",  # rule score 30
        status="open",
        related_asset_id="RISK-001"
    )
    db_session.add(inc)
    db_session.commit()

    # Create some events for ML
    now = datetime.utcnow()
    for i in range(5):
        db_session.add(Event(
            event_id=f"E-RISK-{i}",
            asset_id="RISK-001",
            event_type="login_failed",
            timestamp=now - timedelta(minutes=i)
        ))
    db_session.commit()

    # Test rule score calculation
    rule_score = _calculate_rule_score(db_session, "RISK-001")
    assert rule_score == SEVERITY_TO_RULE_SCORE["High"]  # 30

    # Test severity mapping
    assert _map_score_to_severity(25) == "Low"
    assert _map_score_to_severity(45) == "Medium"
    assert _map_score_to_severity(70) == "High"
    assert _map_score_to_severity(90) == "Critical"

    # Run full risk scan
    scores = run_risk_scan(db_session)
    assert len(scores) == 1
    score_obj = scores[0]
    assert score_obj.asset_id == "RISK-001"
    assert score_obj.rule_score == 30.0
    assert score_obj.criticality_weight == CRITICALITY_TO_WEIGHT["Critical"]  # 20
    assert score_obj.total_score == 30 + score_obj.ml_score + 20


def test_endpoints_ml_anomalies(client):
    # First, create some assets and events via API
    assets = [
        {"name": "Test Asset 1", "asset_type": "server", "criticality": "Critical"},
        {"name": "Test Asset 2", "asset_type": "endpoint", "criticality": "Low"}
    ]
    response = client.post("/upload-assets", json={"assets": assets})
    assert response.status_code == 200
    asset_ids = response.json()["asset_ids"]

    # Simulate a bruteforce attack on the first asset
    response = client.post("/simulate/bruteforce", json={"asset_id": asset_ids[0], "intensity": 100})
    assert response.status_code == 200

    # Test ML anomalies endpoint
    response = client.get("/ml/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "asset_count" in data
    assert "assets" in data


def test_endpoints_risk_scores(client):
    # Test risk scan endpoint
    response = client.post("/risk/scan")
    assert response.status_code == 200

    # Test get risk scores endpoint
    response = client.get("/risk")
    assert response.status_code == 200
    data = response.json()
    assert "asset_count" in data
    assert "assets" in data
