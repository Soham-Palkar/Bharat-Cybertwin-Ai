"""
Tests for Module 3 (Attack Injection / Simulate endpoints)
and Module 4 (Detection Engine / Incidents endpoints).
"""

import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Asset, Event, Incident
from backend.app.services.detection import run_detection_scan

# ---------------------------------------------------------------------------
# Test DB setup
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_asset(db_session) -> str:
    """Insert a test asset and return its asset_id."""
    asset = Asset(
        asset_id="AST-1001",
        name="DB01",
        asset_type="database",
        ip_address="10.0.1.5",
        criticality="Critical",
        owner="db-owner",
    )
    db_session.add(asset)
    db_session.commit()
    return asset.asset_id


# ===========================================================================
# MODULE 3 — Simulation endpoint tests
# ===========================================================================

class TestSimulateBruteforce:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["attack_type"] == "bruteforce"
        assert data["target_asset_id"] == "AST-1001"
        assert data["events_generated"] >= 60

        events = db_session.query(Event).filter(
            Event.asset_id == "AST-1001",
            Event.event_type == "login_failed",
        ).all()
        assert len(events) >= 60

    def test_custom_intensity(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/bruteforce", json={"asset_id": "AST-1001", "intensity": 80})
        data = resp.json()
        assert data["events_generated"] == 80

    def test_random_asset_when_none_given(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/bruteforce")
        assert resp.status_code == 200
        assert resp.json()["target_asset_id"] == "AST-1001"

    def test_error_no_assets(self, client, db_session):
        resp = client.post("/simulate/bruteforce")
        assert resp.status_code == 400


class TestSimulateCredentialStuffing:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/credential-stuffing", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["attack_type"] == "credential-stuffing"
        assert data["events_generated"] > 0


class TestSimulateImpossibleTravel:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/impossible-travel", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["events_generated"] == 2  # exactly 2 logins


class TestSimulatePortScan:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/port-scan", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["events_generated"] >= 30


class TestSimulateInsiderThreat:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/insider-threat", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        assert resp.json()["events_generated"] > 0


class TestSimulateExfiltration:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/exfiltration", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        assert resp.json()["events_generated"] > 0


class TestSimulatePhishing:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/phishing", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        assert resp.json()["events_generated"] > 0


class TestSimulatePrivilegeEscalation:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/privilege-escalation", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        assert resp.json()["events_generated"] > 0


class TestSimulateRansomware:
    def test_produces_events(self, client, db_session):
        _seed_asset(db_session)
        resp = client.post("/simulate/ransomware", json={"asset_id": "AST-1001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["events_generated"] >= 25


# ===========================================================================
# MODULE 4 — Detection & Incident tests
# ===========================================================================

class TestDetectionBruteforce:
    def test_bruteforce_creates_incident(self, client, db_session):
        _seed_asset(db_session)
        # Inject brute-force events
        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        # Run detection
        resp = client.post("/detect/run-now")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["incidents_created"] >= 1

        # Verify incident details
        found = False
        for inc in data["incidents"]:
            if "Brute-Force" in inc["title"]:
                assert inc["severity"] == "High"
                assert inc["status"] == "open"
                assert inc["related_asset_id"] == "AST-1001"
                found = True
        assert found, "Expected a Brute-Force incident but none was found"

    def test_duplicate_suppression(self, client, db_session):
        _seed_asset(db_session)
        # Inject brute-force events twice
        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        client.post("/detect/run-now")

        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        resp2 = client.post("/detect/run-now")
        data2 = resp2.json()

        # Second detection should NOT create a duplicate brute-force incident
        bf_incidents = [i for i in data2["incidents"] if "Brute-Force" in i["title"]]
        assert len(bf_incidents) == 0, "Duplicate brute-force incident was created"

        # Only one brute-force incident should exist in total
        all_incidents = db_session.query(Incident).filter(
            Incident.title == "Brute-Force Login Detected",
            Incident.related_asset_id == "AST-1001",
        ).all()
        assert len(all_incidents) == 1


class TestDetectionRansomware:
    def test_ransomware_creates_critical_incident(self, client, db_session):
        _seed_asset(db_session)
        client.post("/simulate/ransomware", json={"asset_id": "AST-1001"})
        resp = client.post("/detect/run-now")
        data = resp.json()

        found = False
        for inc in data["incidents"]:
            if "Ransomware" in inc["title"]:
                assert inc["severity"] == "Critical"
                found = True
        assert found, "Expected a Ransomware incident but none was found"

    def test_exfiltration_and_background_do_not_trigger_ransomware(
        self, client, db_session
    ):
        """Exfiltration + synthetic background traffic must not hit the 20-event threshold."""
        from datetime import datetime, timedelta

        _seed_asset(db_session)
        client.post("/simulate/exfiltration", json={"asset_id": "AST-1001"})

        now = datetime.utcnow()
        background_types = ["vpn_connection", "firewall_allow", "system_auth"]
        for i in range(25):
            db_session.add(
                Event(
                    event_id=f"EVT-BG{i:03d}",
                    asset_id="AST-1001",
                    source_ip="192.168.1.15",
                    event_type=background_types[i % 3],
                    raw_payload="Synthetic background log",
                    timestamp=now - timedelta(seconds=i * 10),
                )
            )
        db_session.commit()

        resp = client.post("/detect/run-now")
        data = resp.json()
        ransomware_incidents = [
            inc for inc in data["incidents"] if "Ransomware" in inc["title"]
        ]
        assert ransomware_incidents == []


class TestGetIncidents:
    def test_get_all_incidents(self, client, db_session):
        _seed_asset(db_session)
        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        client.post("/detect/run-now")

        resp = client.get("/incidents")
        assert resp.status_code == 200
        incidents = resp.json()
        assert len(incidents) >= 1

    def test_filter_by_status(self, client, db_session):
        _seed_asset(db_session)
        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        client.post("/detect/run-now")

        resp_open = client.get("/incidents?status=open")
        assert resp_open.status_code == 200
        assert len(resp_open.json()) >= 1

        resp_closed = client.get("/incidents?status=closed")
        assert resp_closed.status_code == 200
        assert len(resp_closed.json()) == 0

    def test_filter_by_severity(self, client, db_session):
        _seed_asset(db_session)
        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        client.post("/detect/run-now")

        resp_high = client.get("/incidents?severity=High")
        assert resp_high.status_code == 200
        assert len(resp_high.json()) >= 1

        resp_low = client.get("/incidents?severity=Low")
        assert resp_low.status_code == 200
        # May or may not have Low incidents — just check it doesn't error

    def test_newest_first(self, client, db_session):
        _seed_asset(db_session)
        client.post("/simulate/bruteforce", json={"asset_id": "AST-1001"})
        client.post("/simulate/ransomware", json={"asset_id": "AST-1001"})
        client.post("/detect/run-now")

        resp = client.get("/incidents")
        incidents = resp.json()
        if len(incidents) >= 2:
            # Verify newest first
            assert incidents[0]["created_at"] >= incidents[-1]["created_at"]
