import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app import models

from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
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

def test_upload_assets_json(client):
    payload = {
        "assets": [
            { "name": "DB02", "asset_type": "database", "ip_address": "10.0.1.6", "criticality": "Critical" },
            { "name": "VPN-GW-02", "asset_type": "vpn", "ip_address": "10.0.0.3", "criticality": "High" }
        ]
    }
    response = client.post("/upload-assets", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["imported"] == 2
    assert len(data["asset_ids"]) == 2
    assert data["asset_ids"] == ["AST-1001", "AST-1002"]

def test_upload_assets_csv(client):
    csv_data = (
        "name,asset_type,ip_address,criticality,owner\n"
        "DB01,database,10.0.1.5,Critical,db-owner\n"
        "VPN-GW,vpn,10.0.0.1,High,net-admin\n"
        "WEB01,server,10.0.1.10,Medium,web-dev\n"
    )
    
    files = {"file": ("sample_assets.csv", csv_data, "text/csv")}
    response = client.post("/upload-assets", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["imported"] == 3
    assert len(data["asset_ids"]) == 3
    assert data["asset_ids"] == ["AST-1001", "AST-1002", "AST-1003"]

def test_upload_assets_validation_errors(client):
    # Missing required field 'name'
    csv_data_missing_name = (
        "name,asset_type,ip_address,criticality,owner\n"
        ",database,10.0.1.5,Critical,db-owner\n"
    )
    files = {"file": ("assets.csv", csv_data_missing_name, "text/csv")}
    response = client.post("/upload-assets", files=files)
    assert response.status_code == 400
    assert "missing required field 'name'" in response.json()["detail"].lower()

    # Invalid criticality
    csv_data_invalid_crit = (
        "name,asset_type,ip_address,criticality,owner\n"
        "DB01,database,10.0.1.5,SuperCritical,db-owner\n"
    )
    files = {"file": ("assets.csv", csv_data_invalid_crit, "text/csv")}
    response = client.post("/upload-assets", files=files)
    assert response.status_code == 400
    assert "invalid criticality" in response.json()["detail"].lower()

def test_get_assets_sorted(client):
    csv_data = (
        "name,asset_type,ip_address,criticality,owner\n"
        "WEB01,server,10.0.1.10,Medium,web-dev\n"
        "DB01,database,10.0.1.5,Critical,db-owner\n"
        "WORK05,endpoint,10.0.2.55,Low,hr-dept\n"
        "VPN-GW,vpn,10.0.0.1,High,net-admin\n"
    )
    files = {"file": ("assets.csv", csv_data, "text/csv")}
    upload_res = client.post("/upload-assets", files=files)
    assert upload_res.status_code == 200

    get_res = client.get("/assets")
    assert get_res.status_code == 200
    assets = get_res.json()
    assert len(assets) == 4
    
    assert assets[0]["criticality"] == "Critical"
    assert assets[0]["name"] == "DB01"
    
    assert assets[1]["criticality"] == "High"
    assert assets[1]["name"] == "VPN-GW"
    
    assert assets[2]["criticality"] == "Medium"
    assert assets[2]["name"] == "WEB01"
    
    assert assets[3]["criticality"] == "Low"
    assert assets[3]["name"] == "WORK05"
