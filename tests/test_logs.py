import os
os.environ["TESTING"] = "1"

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Asset, Event

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

def test_websocket_logs_broadcast(client):
    with client.websocket_connect("/ws/logs") as websocket:
        from backend.app.routers.logs import manager
        
        event_payload = {
            "event_id": "EVT-TEST",
            "asset_id": "AST-1001",
            "source_ip": "192.168.1.15",
            "event_type": "vpn_connection",
            "raw_payload": "VPN connection established",
            "timestamp": "2026-06-20T12:00:00"
        }
        
        # Broadcast directly to all sockets
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manager.broadcast(event_payload))
        
        # WebSocket client should receive it
        received = websocket.receive_json()
        assert received == event_payload

def test_synthetic_log_generator_logic(db_session):
    # 1. Insert an asset
    asset = Asset(
        asset_id="AST-1001",
        name="DB01",
        asset_type="database",
        ip_address="10.0.1.5",
        criticality="Critical",
        owner="db-owner"
    )
    db_session.add(asset)
    db_session.commit()
    
    # 2. Patch SessionLocal in services.synthetic_logs to use memory DB
    import backend.app.services.synthetic_logs as sl
    
    original_sleep = asyncio.sleep
    call_count = 0
    
    # Mock sleep to execute exactly once and then raise CancelledError to stop the loop
    async def mock_sleep(seconds):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise asyncio.CancelledError()
        return

    asyncio.sleep = mock_sleep
    original_sl = sl.SessionLocal
    sl.SessionLocal = TestingSessionLocal
    
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(sl.run_synthetic_log_generator())
    finally:
        asyncio.sleep = original_sleep
        sl.SessionLocal = original_sl
        
    # Check if a new Event was inserted in DB
    events = db_session.query(Event).all()
    assert len(events) == 1
    event = events[0]
    assert event.asset_id == "AST-1001"
    assert event.event_type in ("vpn_connection", "firewall_allow", "system_auth")
    assert event.raw_payload is not None
