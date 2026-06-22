"""Debug script for the two bugs!"""
import sys
from datetime import datetime, timedelta
sys.path.insert(0, 'backend')

from app.database import SessionLocal, engine, Base
from app.models import Asset, Event, Incident, RiskScore
from app.routers.assets import upload_assets
from app.services.attack_injection import inject_bruteforce, inject_exfiltration, inject_ransomware
from app.services.detection import run_detection_scan
from app.services.risk_engine import run_risk_scan

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    print("\n=== 1. Uploading real assets ===")
    # Upload real assets (DB01, FW01, etc.)
    real_assets = [
        {"name": "DB01", "asset_type": "database", "ip_address": "10.0.1.10", "criticality": "Critical"},
        {"name": "FW01", "asset_type": "firewall", "ip_address": "10.0.0.1", "criticality": "High"},
        {"name": "WS01", "asset_type": "workstation", "ip_address": "192.168.1.50", "criticality": "Low"},
    ]
    # We need to simulate what upload_assets does, so let's create Asset objects directly
    import uuid
    for asset_data in real_assets:
        asset = Asset(
            asset_id=f"AST-{uuid.uuid4().hex[:8].upper()}",
            name=asset_data["name"],
            asset_type=asset_data["asset_type"],
            ip_address=asset_data["ip_address"],
            criticality=asset_data["criticality"],
        )
        db.add(asset)
    db.commit()
    assets = db.query(Asset).all()
    for a in assets:
        print(f" - {a.asset_id}: {a.name} ({a.criticality})")

    print("\n=== 2. Injecting attacks ===")
    # Inject brute force on DB01
    db01 = next(a for a in assets if a.name == "DB01")
    asset_id, events = inject_bruteforce(db, db01.asset_id, 65)
    print(f" - Injected {len(events)} brute-force events on {db01.name}")
    
    # Inject exfiltration and ransomware on FW01
    fw01 = next(a for a in assets if a.name == "FW01")
    asset_id, events = inject_exfiltration(db, fw01.asset_id)
    print(f" - Injected {len(events)} exfiltration events on {fw01.name}")
    asset_id, events = inject_ransomware(db, fw01.asset_id)
    print(f" - Injected {len(events)} ransomware events on {fw01.name}")

    print("\n=== 3. Checking event timestamps ===")
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    print(f"Detection window cutoff: {cutoff.isoformat()}")
    recent_events = db.query(Event).filter(Event.timestamp >= cutoff).all()
    print(f"Total events in window: {len(recent_events)}")
    for evt in recent_events[:5]:  # show first 5
        print(f" - {evt.event_type} at {evt.timestamp.isoformat()} (asset {evt.asset_id})")

    print("\n=== 4. Running detection scan ===")
    new_incidents = run_detection_scan(db)
    print(f"Created {len(new_incidents)} new incidents!")
    for inc in new_incidents:
        print(f" - {inc.incident_id}: {inc.title} ({inc.severity}) on {inc.related_asset_id}")

    print("\n=== 5. All incidents in DB ===")
    all_incidents = db.query(Incident).all()
    for inc in all_incidents:
        print(f" - {inc.incident_id}: {inc.title}, related_asset={inc.related_asset_id}, status={inc.status}, severity={inc.severity}")

    print("\n=== 6. Running risk scan ===")
    new_scores = run_risk_scan(db)
    print(f"Saved {len(new_scores)} risk scores")

    print("\n=== 7. Latest Risk Scores ===")
    for score in new_scores:
        asset = db.query(Asset).filter(Asset.asset_id == score.asset_id).first()
        print(f" - Asset {score.asset_id} ({asset.name if asset else '???'}):")
        print(f"   - rule_score: {score.rule_score}")
        print(f"   - ml_score: {score.ml_score}")
        print(f"   - total_score: {score.total_score}")
        print(f"   - severity: {score.severity}")

    print("\n=== 8. Check rule score calculation for FW01 ===")
    from app.services.risk_engine import _calculate_rule_score
    fw_rule_score = _calculate_rule_score(db, fw01.asset_id)
    print(f"FW01 rule score (direct call): {fw_rule_score}")

finally:
    db.close()
