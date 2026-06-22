import asyncio
import logging
import random
import uuid
from datetime import datetime
from ..database import SessionLocal
from ..models import Asset, Event
from ..routers.logs import manager

logger = logging.getLogger("cybertwin.synthetic_logs")

# Sample values for realistic logs
USERNAMES = ["alice.security", "bob.developer", "admin", "dev_svc", "backup_agent", "hr_system"]
IPS = ["192.168.1.15", "192.168.1.24", "10.0.2.11", "10.0.2.12", "172.16.5.4", "172.16.5.9"]
PORTS = [22, 80, 443, 3306, 5432, 8080, 2222]

async def run_synthetic_log_generator():
    logger.info("Synthetic log generator background task started.")
    while True:
        try:
            # Sleep for a random interval between 2 and 5 seconds
            await asyncio.sleep(random.uniform(2.0, 5.0))

            with SessionLocal() as db:
                assets = db.query(Asset).all()
                if not assets:
                    logger.warning("No assets found in the database. Skipping synthetic log generation.")
                    continue

                asset = random.choice(assets)
                event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
                source_ip = random.choice(IPS)
                event_style = random.choice(["vpn", "firewall", "auth"])
                username = random.choice(USERNAMES)
                now = datetime.utcnow()

                if event_style == "vpn":
                    event_type = "vpn_connection"
                    raw_payload = f"VPN connection established from {source_ip}: user '{username}', status 'Success'"
                elif event_style == "firewall":
                    event_type = "firewall_allow"
                    sport = random.randint(1024, 65535)
                    dport = random.choice(PORTS)
                    raw_payload = f"Firewall packet allowed: SRC={source_ip} DST={asset.ip_address or '0.0.0.0'} PROTO=TCP SPT={sport} DPT={dport}"
                else:  # auth
                    event_type = "system_auth"
                    sport = random.randint(1024, 65535)
                    pid = random.randint(1000, 9999)
                    time_str = now.strftime("%b %d %H:%M:%S")
                    raw_payload = f"{time_str} localhost sshd[{pid}]: Accepted publickey for {username} from {source_ip} port {sport} ssh2"

                db_event = Event(
                    event_id=event_id,
                    asset_id=asset.asset_id,
                    source_ip=source_ip,
                    event_type=event_type,
                    raw_payload=raw_payload,
                    timestamp=now
                )
                db.add(db_event)
                db.commit()

                event_data = {
                    "event_id": event_id,
                    "asset_id": asset.asset_id,
                    "source_ip": source_ip,
                    "event_type": event_type,
                    "raw_payload": raw_payload,
                    "timestamp": now.isoformat()
                }
                await manager.broadcast(event_data)

        except asyncio.CancelledError:
            logger.info("Synthetic log generator background task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in synthetic log generator: {str(e)}", exc_info=True)
