"""
Module 3 — Attack Injection Engine

Generates labeled, attack-shaped telemetry bursts and writes them directly
into the Events table.  Each function produces enough events in a single
call to cross the matching detection-rule threshold so that a subsequent
detection scan will immediately fire an incident.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from ..models import Asset, Event

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_ATTACKER_IPS = [
    "45.33.32.156", "198.51.100.23", "203.0.113.42",
    "185.220.101.9", "91.219.237.18", "77.247.181.163",
]

_USERNAMES = [
    "alice.security", "bob.developer", "carol.finance",
    "dave.hr", "eve.marketing", "frank.ops",
    "grace.devops", "heidi.intern", "ivan.sales",
    "judy.support",
]

_ADMIN_USERNAMES = ["admin", "root", "sysadmin"]

_GEO_LOCATIONS = [
    ("Mumbai, IN", "103.21.58.10"),
    ("New York, US", "198.51.100.23"),
    ("London, UK", "203.0.113.42"),
    ("Tokyo, JP", "45.33.32.156"),
    ("Sydney, AU", "91.219.237.18"),
    ("Berlin, DE", "77.247.181.163"),
]

_SUSPICIOUS_URLS = [
    "http://secure-login-update.xyz/reset",
    "http://acc0unt-verify.tk/login",
    "http://paypa1-secure.ml/confirm",
    "http://micros0ft-alert.ga/action",
]

_FILE_EXTENSIONS = [
    ".docx", ".xlsx", ".pdf", ".pptx", ".sql", ".bak",
    ".csv", ".json", ".zip", ".tar.gz", ".jpg", ".png",
]


def _gen_event_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:8].upper()}"


def _pick_attacker_ip() -> str:
    return random.choice(_ATTACKER_IPS)


def _random_asset(db: Session) -> Asset:
    """Pick a random existing asset from the database."""
    assets = db.query(Asset).all()
    if not assets:
        raise ValueError("No assets in the database. Upload assets first.")
    return random.choice(assets)


def _resolve_asset(db: Session, asset_id: str | None) -> Asset:
    """Return the requested asset or pick a random one."""
    if asset_id:
        asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")
        return asset
    return _random_asset(db)


# ---------------------------------------------------------------------------
# 1. Brute-Force  (60+ failed logins from one source_ip)
# ---------------------------------------------------------------------------
def inject_bruteforce(db: Session, asset_id: str | None = None,
                      intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    count = intensity or 65
    src_ip = _pick_attacker_ip()
    username = random.choice(_USERNAMES)
    now = datetime.utcnow()
    events: list[Event] = []

    for i in range(count):
        ts = now - timedelta(seconds=random.randint(0, 240))
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="login_failed",
            raw_payload=(
                f"sshd[{random.randint(1000,9999)}]: Failed password for "
                f"{username} from {src_ip} port {random.randint(1024,65535)} ssh2"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 2. Credential Stuffing  (one source_ip → many distinct users)
# ---------------------------------------------------------------------------
def inject_credential_stuffing(db: Session, asset_id: str | None = None,
                               intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    src_ip = _pick_attacker_ip()
    num_users = intensity or 12
    now = datetime.utcnow()
    events: list[Event] = []

    # Pick distinct usernames
    targets = random.sample(_USERNAMES, min(num_users, len(_USERNAMES)))
    if num_users > len(_USERNAMES):
        targets += [f"user{i}@corp" for i in range(num_users - len(_USERNAMES))]

    for username in targets:
        # 3-5 attempts per user
        for _ in range(random.randint(3, 5)):
            ts = now - timedelta(seconds=random.randint(0, 240))
            evt = Event(
                event_id=_gen_event_id(),
                asset_id=asset.asset_id,
                source_ip=src_ip,
                event_type="login_failed",
                raw_payload=(
                    f"sshd[{random.randint(1000,9999)}]: Failed password for "
                    f"{username} from {src_ip} port {random.randint(1024,65535)} ssh2 "
                    f"[credential-stuffing pattern: distinct user]"
                ),
                timestamp=ts,
            )
            db.add(evt)
            events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 3. Impossible Travel  (same user, two geolocations, minutes apart)
# ---------------------------------------------------------------------------
def inject_impossible_travel(db: Session, asset_id: str | None = None,
                             intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    username = random.choice(_USERNAMES)
    now = datetime.utcnow()
    events: list[Event] = []

    loc_a, ip_a = random.choice(_GEO_LOCATIONS)
    loc_b, ip_b = random.choice([g for g in _GEO_LOCATIONS if g[0] != loc_a])

    # First login
    evt1 = Event(
        event_id=_gen_event_id(),
        asset_id=asset.asset_id,
        source_ip=ip_a,
        event_type="login_success",
        raw_payload=(
            f"Successful login for {username} from {ip_a} "
            f"[geo: {loc_a}]"
        ),
        timestamp=now - timedelta(minutes=3),
    )
    db.add(evt1)
    events.append(evt1)

    # Second login from different geo, minutes later
    evt2 = Event(
        event_id=_gen_event_id(),
        asset_id=asset.asset_id,
        source_ip=ip_b,
        event_type="login_success",
        raw_payload=(
            f"Successful login for {username} from {ip_b} "
            f"[geo: {loc_b}]"
        ),
        timestamp=now,
    )
    db.add(evt2)
    events.append(evt2)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 4. Port Scan  (many distinct ports from one source_ip)
# ---------------------------------------------------------------------------
def inject_port_scan(db: Session, asset_id: str | None = None,
                     intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    count = intensity or 40
    src_ip = _pick_attacker_ip()
    now = datetime.utcnow()
    events: list[Event] = []
    ports = random.sample(range(1, 65536), min(count, 65535))

    for port in ports[:count]:
        ts = now - timedelta(seconds=random.randint(0, 120))
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="port_scan",
            raw_payload=(
                f"Firewall SYN packet: SRC={src_ip} DST={asset.ip_address or '10.0.0.1'} "
                f"PROTO=TCP DPT={port} [port-scan probe]"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 5. Insider Threat  (off-hours + unusual asset access)
# ---------------------------------------------------------------------------
def inject_insider_threat(db: Session, asset_id: str | None = None,
                          intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    count = intensity or 8
    username = random.choice(_USERNAMES)
    src_ip = random.choice(["192.168.1.15", "10.0.2.11"])
    events: list[Event] = []

    # Generate events at off-hours (e.g. 2 AM - 4 AM)
    base_time = datetime.utcnow().replace(hour=2, minute=30, second=0)
    for i in range(count):
        ts = base_time + timedelta(minutes=random.randint(0, 90))
        actions = [
            f"User {username} accessed sensitive file /data/financials/Q4_report.xlsx",
            f"User {username} downloaded database backup from {asset.name}",
            f"User {username} accessed restricted directory /admin/configs/",
            f"User {username} queried customer PII table on {asset.name}",
        ]
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="user_access",
            raw_payload=(
                f"{ts.strftime('%b %d %H:%M:%S')} {random.choice(actions)} "
                f"[off-hours activity from {src_ip}]"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 6. Data Exfiltration  (large download/transfer events)
# ---------------------------------------------------------------------------
def inject_exfiltration(db: Session, asset_id: str | None = None,
                        intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    count = intensity or 6
    src_ip = random.choice(["192.168.1.15", "10.0.2.11"])
    username = random.choice(_USERNAMES)
    now = datetime.utcnow()
    events: list[Event] = []

    for i in range(count):
        ts = now - timedelta(seconds=random.randint(0, 200))
        bytes_transferred = random.randint(800_000_000, 2_000_000_000)  # 800MB-2GB each
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="data_transfer",
            raw_payload=(
                f"Large data transfer by {username}: {bytes_transferred} bytes "
                f"transferred from {asset.name} to external endpoint 45.33.32.156 "
                f"via HTTPS [volume: {bytes_transferred / 1_000_000:.0f} MB]"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 7. Phishing  (suspicious referrer → anomalous activity)
# ---------------------------------------------------------------------------
def inject_phishing(db: Session, asset_id: str | None = None,
                    intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    username = random.choice(_USERNAMES)
    src_ip = _pick_attacker_ip()
    now = datetime.utcnow()
    events: list[Event] = []
    phish_url = random.choice(_SUSPICIOUS_URLS)

    # 1) Login with suspicious referrer
    evt1 = Event(
        event_id=_gen_event_id(),
        asset_id=asset.asset_id,
        source_ip=src_ip,
        event_type="login_success",
        raw_payload=(
            f"Login for {username} from {src_ip} "
            f"referrer={phish_url} [suspicious-url]"
        ),
        timestamp=now - timedelta(seconds=120),
    )
    db.add(evt1)
    events.append(evt1)

    # 2) Follow-up anomalous activity from that session
    follow_count = intensity or 5
    for i in range(follow_count):
        ts = now - timedelta(seconds=random.randint(0, 100))
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="user_access",
            raw_payload=(
                f"Post-phishing activity: {username} accessed {asset.name} "
                f"resource /api/internal/users referrer={phish_url} [suspicious-url]"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 8. Privilege Escalation  (normal user → admin actions)
# ---------------------------------------------------------------------------
def inject_privilege_escalation(db: Session, asset_id: str | None = None,
                                intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    # Pick a non-admin user
    username = random.choice(_USERNAMES)
    src_ip = random.choice(["192.168.1.15", "10.0.2.11"])
    now = datetime.utcnow()
    events: list[Event] = []
    count = intensity or 5

    admin_actions = [
        f"User {username} executed: sudo useradd backdoor_user",
        f"User {username} modified /etc/sudoers on {asset.name}",
        f"User {username} changed firewall rule: iptables -A INPUT -p tcp --dport 4444 -j ACCEPT",
        f"User {username} reset admin password on {asset.name}",
        f"User {username} granted root privileges to account svc_hidden",
        f"User {username} disabled audit logging on {asset.name}",
    ]

    for i in range(count):
        ts = now - timedelta(seconds=random.randint(0, 180))
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="admin_action",
            raw_payload=(
                f"{random.choice(admin_actions)} "
                f"[non-admin user performing admin action]"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events


# ---------------------------------------------------------------------------
# 9. Ransomware  (rapid file access / modification burst)
# ---------------------------------------------------------------------------
def inject_ransomware(db: Session, asset_id: str | None = None,
                      intensity: int | None = None) -> tuple[str, List[Event]]:
    asset = _resolve_asset(db, asset_id)
    count = intensity or 30
    src_ip = random.choice(["192.168.1.15", "10.0.2.11"])
    now = datetime.utcnow()
    events: list[Event] = []

    for i in range(count):
        ts = now - timedelta(seconds=random.randint(0, 60))
        ext = random.choice(_FILE_EXTENSIONS)
        filename = f"/data/shared/document_{random.randint(1000,9999)}{ext}"
        action = random.choice(["encrypted", "modified", "renamed", "accessed"])
        evt = Event(
            event_id=_gen_event_id(),
            asset_id=asset.asset_id,
            source_ip=src_ip,
            event_type="file_action",
            raw_payload=(
                f"File {action}: {filename} → {filename}.locked "
                f"by process cryptor.exe on {asset.name} "
                f"[rapid file modification pattern]"
            ),
            timestamp=ts,
        )
        db.add(evt)
        events.append(evt)

    db.commit()
    return asset.asset_id, events
