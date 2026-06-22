"""
Module 4 — Detection Engine (rule-based)

Scans recent Events for patterns matching known attack types and creates
Incidents when a rule fires.  Duplicate suppression ensures that only one
open incident per (asset, rule title) exists at any time.

All tuneable thresholds are defined as module-level constants at the top of
this file.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Event, Incident

logger = logging.getLogger("cybertwin.detection")

# ===================================================================
# TUNEABLE THRESHOLDS — edit these to adjust detection sensitivity
# ===================================================================

DETECTION_WINDOW_MINUTES = 5
"""How far back (in minutes) each scan looks for matching events."""

THRESHOLD_BRUTEFORCE = 50
"""Failed logins from the same source_ip to trigger brute-force rule."""

THRESHOLD_CRED_STUFFING_USERS = 5
"""Distinct usernames targeted from the same source_ip for credential stuffing."""

THRESHOLD_PORT_SCAN = 30
"""Distinct port-touch events from one source_ip against one asset."""

THRESHOLD_EXFILTRATION_BYTES = 5_000_000_000
"""Total bytes transferred from an asset to trigger exfiltration rule (5 GB)."""

THRESHOLD_RANSOMWARE_FILES = 20
"""File-action events on the same asset to trigger ransomware rule."""

RANSOMWARE_EVENT_TYPE = "file_action"
"""event_type written exclusively by inject_ransomware (attack_injection.py)."""

RANSOMWARE_PAYLOAD_MARKER = "[rapid file modification pattern]"
"""Signature string present in every ransomware-injector payload."""

BUSINESS_HOURS_START = 9   # 09:00
BUSINESS_HOURS_END = 18    # 18:00
"""Business hours range (UTC) used by the off-hours rule."""

SUSPICIOUS_URL_PATTERNS = [
    r"secure-login-update",
    r"acc0unt-verify",
    r"paypa1-secure",
    r"micros0ft-alert",
    r"\[suspicious-url\]",
]
"""Regex patterns matched against raw_payload for the phishing rule."""

ADMIN_USERNAMES = {"admin", "root", "sysadmin"}
"""Usernames considered legitimate admin accounts (privilege-escalation rule
only fires for users NOT in this set)."""

BACKGROUND_SCAN_INTERVAL_SECONDS = 10
"""How often the background detection loop runs."""


# ===================================================================
# CORE DETECTION SCAN
# ===================================================================

def run_detection_scan(db: Session) -> list[Incident]:
    """
    Execute all nine detection rules against events within the scan
    window.  Returns the list of newly created Incidents.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=DETECTION_WINDOW_MINUTES)
    new_incidents: list[Incident] = []

    new_incidents.extend(_rule_bruteforce(db, cutoff))
    new_incidents.extend(_rule_credential_stuffing(db, cutoff))
    new_incidents.extend(_rule_port_scan(db, cutoff))
    new_incidents.extend(_rule_impossible_travel(db, cutoff))
    new_incidents.extend(_rule_exfiltration(db, cutoff))
    new_incidents.extend(_rule_privilege_escalation(db, cutoff))
    new_incidents.extend(_rule_off_hours(db, cutoff))
    new_incidents.extend(_rule_phishing(db, cutoff))
    new_incidents.extend(_rule_ransomware(db, cutoff))

    if new_incidents:
        db.commit()
        logger.info("Detection scan created %d new incident(s).", len(new_incidents))
    else:
        logger.debug("Detection scan completed — no new incidents.")

    return new_incidents


# ===================================================================
# BACKGROUND LOOP
# ===================================================================

async def run_detection_background_loop() -> None:
    """Runs detection scans on a periodic schedule."""
    logger.info("Detection background loop started (interval=%ds).",
                BACKGROUND_SCAN_INTERVAL_SECONDS)
    while True:
        try:
            await asyncio.sleep(BACKGROUND_SCAN_INTERVAL_SECONDS)
            with SessionLocal() as db:
                run_detection_scan(db)
        except asyncio.CancelledError:
            logger.info("Detection background loop cancelled.")
            break
        except Exception:
            logger.exception("Error in detection background loop")


# ===================================================================
# HELPER: duplicate suppression
# ===================================================================

def _incident_exists(db: Session, title: str, asset_id: str) -> bool:
    """Return True if an open incident with this title+asset already exists."""
    return (
        db.query(Incident)
        .filter(
            Incident.title == title,
            Incident.related_asset_id == asset_id,
            Incident.status == "open",
        )
        .first()
        is not None
    )


def _create_incident(db: Session, title: str, description: str,
                     severity: str, asset_id: str) -> Incident | None:
    """Create an incident if one doesn't already exist for this rule/asset."""
    if _incident_exists(db, title, asset_id):
        return None
    inc = Incident(
        incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
        title=title,
        description=description,
        severity=severity,
        status="open",
        related_asset_id=asset_id,
        created_at=datetime.utcnow(),
    )
    db.add(inc)
    return inc


# ===================================================================
# INDIVIDUAL RULES
# ===================================================================

def _rule_bruteforce(db: Session, cutoff: datetime) -> list[Incident]:
    """Failed logins > THRESHOLD from same source_ip on same asset."""
    rows = (
        db.query(Event.asset_id, Event.source_ip, func.count(Event.event_id))
        .filter(Event.event_type == "login_failed", Event.timestamp >= cutoff)
        .group_by(Event.asset_id, Event.source_ip)
        .having(func.count(Event.event_id) > THRESHOLD_BRUTEFORCE)
        .all()
    )
    incidents = []
    for asset_id, src_ip, cnt in rows:
        title = "Brute-Force Login Detected"
        desc = (
            f"Detected {cnt} failed login attempts from source IP {src_ip} "
            f"against asset {asset_id} within the last {DETECTION_WINDOW_MINUTES} "
            f"minutes. This exceeds the threshold of {THRESHOLD_BRUTEFORCE} "
            f"and indicates a possible brute-force attack."
        )
        inc = _create_incident(db, title, desc, "High", asset_id)
        if inc:
            incidents.append(inc)
    return incidents


def _rule_credential_stuffing(db: Session, cutoff: datetime) -> list[Incident]:
    """Same source_ip targeting > THRESHOLD distinct usernames."""
    events = (
        db.query(Event)
        .filter(Event.event_type == "login_failed", Event.timestamp >= cutoff)
        .all()
    )
    # Group by (asset_id, source_ip) → set of usernames
    groups: dict[tuple[str, str], set[str]] = {}
    for evt in events:
        key = (evt.asset_id, evt.source_ip)
        if key not in groups:
            groups[key] = set()
        # Extract username from payload
        if evt.raw_payload:
            m = re.search(r"Failed password for (\S+)", evt.raw_payload)
            if m:
                groups[key].add(m.group(1))

    incidents = []
    for (asset_id, src_ip), users in groups.items():
        if len(users) > THRESHOLD_CRED_STUFFING_USERS:
            title = "Credential Stuffing Detected"
            desc = (
                f"Source IP {src_ip} attempted logins against {len(users)} "
                f"distinct user accounts on asset {asset_id} within the last "
                f"{DETECTION_WINDOW_MINUTES} minutes (threshold: "
                f"{THRESHOLD_CRED_STUFFING_USERS}). Targeted users include: "
                f"{', '.join(sorted(list(users)[:5]))}…"
            )
            inc = _create_incident(db, title, desc, "High", asset_id)
            if inc:
                incidents.append(inc)
    return incidents


def _rule_port_scan(db: Session, cutoff: datetime) -> list[Incident]:
    """Port-touch count over threshold from one source on one asset."""
    rows = (
        db.query(Event.asset_id, Event.source_ip, func.count(Event.event_id))
        .filter(Event.event_type == "port_scan", Event.timestamp >= cutoff)
        .group_by(Event.asset_id, Event.source_ip)
        .having(func.count(Event.event_id) > THRESHOLD_PORT_SCAN)
        .all()
    )
    incidents = []
    for asset_id, src_ip, cnt in rows:
        title = "Port Scan Detected"
        desc = (
            f"Source IP {src_ip} probed {cnt} ports on asset {asset_id} "
            f"within the last {DETECTION_WINDOW_MINUTES} minutes "
            f"(threshold: {THRESHOLD_PORT_SCAN})."
        )
        inc = _create_incident(db, title, desc, "Medium", asset_id)
        if inc:
            incidents.append(inc)
    return incidents


def _rule_impossible_travel(db: Session, cutoff: datetime) -> list[Incident]:
    """Geo anomaly between consecutive logins for the same user."""
    events = (
        db.query(Event)
        .filter(Event.event_type == "login_success", Event.timestamp >= cutoff)
        .order_by(Event.timestamp)
        .all()
    )
    # Group by username extracted from payload
    user_logins: dict[str, list[Event]] = {}
    for evt in events:
        if evt.raw_payload:
            m = re.search(r"(?:login|Login) for (\S+)", evt.raw_payload)
            if m:
                user = m.group(1)
                user_logins.setdefault(user, []).append(evt)

    incidents = []
    for user, logins in user_logins.items():
        for i in range(1, len(logins)):
            prev, curr = logins[i - 1], logins[i]
            if prev.source_ip != curr.source_ip:
                # Extract geo from payload
                geo_prev = re.search(r"\[geo: ([^\]]+)\]", prev.raw_payload or "")
                geo_curr = re.search(r"\[geo: ([^\]]+)\]", curr.raw_payload or "")
                if geo_prev and geo_curr and geo_prev.group(1) != geo_curr.group(1):
                    time_diff = abs((curr.timestamp - prev.timestamp).total_seconds())
                    asset_id = curr.asset_id or prev.asset_id
                    if asset_id:
                        title = "Impossible Travel Detected"
                        desc = (
                            f"User '{user}' logged in from {geo_prev.group(1)} "
                            f"({prev.source_ip}) and then from "
                            f"{geo_curr.group(1)} ({curr.source_ip}) within "
                            f"{time_diff:.0f} seconds — geographically "
                            f"impossible travel."
                        )
                        inc = _create_incident(db, title, desc, "Medium", asset_id)
                        if inc:
                            incidents.append(inc)
    return incidents


def _rule_exfiltration(db: Session, cutoff: datetime) -> list[Incident]:
    """Total transfer volume from an asset exceeds baseline."""
    events = (
        db.query(Event)
        .filter(Event.event_type == "data_transfer", Event.timestamp >= cutoff)
        .all()
    )
    # Aggregate bytes per asset
    asset_bytes: dict[str, int] = {}
    for evt in events:
        if evt.raw_payload:
            m = re.search(r"(\d+) bytes", evt.raw_payload)
            if m:
                asset_bytes[evt.asset_id] = (
                    asset_bytes.get(evt.asset_id, 0) + int(m.group(1))
                )

    incidents = []
    for asset_id, total in asset_bytes.items():
        if total > THRESHOLD_EXFILTRATION_BYTES:
            title = "Data Exfiltration Detected"
            desc = (
                f"Asset {asset_id} transferred {total / 1_000_000_000:.2f} GB "
                f"of data within the last {DETECTION_WINDOW_MINUTES} minutes, "
                f"exceeding the baseline threshold of "
                f"{THRESHOLD_EXFILTRATION_BYTES / 1_000_000_000:.0f} GB."
            )
            inc = _create_incident(db, title, desc, "Critical", asset_id)
            if inc:
                incidents.append(inc)
    return incidents


def _rule_privilege_escalation(db: Session, cutoff: datetime) -> list[Incident]:
    """Non-admin user performing admin-level actions."""
    events = (
        db.query(Event)
        .filter(Event.event_type == "admin_action", Event.timestamp >= cutoff)
        .all()
    )
    # Group by asset, check for non-admin users
    asset_events: dict[str, list[Event]] = {}
    for evt in events:
        asset_events.setdefault(evt.asset_id, []).append(evt)

    incidents = []
    for asset_id, evts in asset_events.items():
        non_admin_actions = []
        for evt in evts:
            if evt.raw_payload:
                m = re.search(r"User (\S+)", evt.raw_payload)
                if m and m.group(1) not in ADMIN_USERNAMES:
                    non_admin_actions.append((m.group(1), evt))
        if non_admin_actions:
            users = set(u for u, _ in non_admin_actions)
            title = "Privilege Escalation Detected"
            desc = (
                f"Non-admin user(s) {', '.join(sorted(users))} performed "
                f"{len(non_admin_actions)} admin-level action(s) on asset "
                f"{asset_id} within the last {DETECTION_WINDOW_MINUTES} minutes."
            )
            inc = _create_incident(db, title, desc, "High", asset_id)
            if inc:
                incidents.append(inc)
    return incidents


def _rule_off_hours(db: Session, cutoff: datetime) -> list[Incident]:
    """Activity outside declared business hours."""
    events = (
        db.query(Event)
        .filter(
            Event.event_type.in_(["login_success", "user_access"]),
            Event.timestamp >= cutoff,
        )
        .all()
    )
    asset_off_hours: dict[str, list[Event]] = {}
    for evt in events:
        if evt.timestamp:
            hour = evt.timestamp.hour
            weekday = evt.timestamp.weekday()  # 0=Mon, 6=Sun
            if weekday >= 5 or hour < BUSINESS_HOURS_START or hour >= BUSINESS_HOURS_END:
                asset_off_hours.setdefault(evt.asset_id, []).append(evt)

    incidents = []
    for asset_id, evts in asset_off_hours.items():
        if len(evts) >= 3:  # Require at least 3 off-hours events to reduce noise
            title = "Off-Hours Activity Detected"
            desc = (
                f"Detected {len(evts)} access events on asset {asset_id} "
                f"outside business hours ({BUSINESS_HOURS_START}:00–"
                f"{BUSINESS_HOURS_END}:00 UTC, Mon–Fri) within the last "
                f"{DETECTION_WINDOW_MINUTES} minutes."
            )
            inc = _create_incident(db, title, desc, "Low", asset_id)
            if inc:
                incidents.append(inc)
    return incidents


def _rule_phishing(db: Session, cutoff: datetime) -> list[Incident]:
    """Access from known-suspicious URL referrer patterns."""
    events = (
        db.query(Event)
        .filter(
            Event.event_type.in_(["login_success", "user_access"]),
            Event.timestamp >= cutoff,
        )
        .all()
    )
    compiled = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_URL_PATTERNS]

    asset_hits: dict[str, int] = {}
    for evt in events:
        if evt.raw_payload:
            for pat in compiled:
                if pat.search(evt.raw_payload):
                    asset_hits[evt.asset_id] = asset_hits.get(evt.asset_id, 0) + 1
                    break

    incidents = []
    for asset_id, count in asset_hits.items():
        if count >= 1:
            title = "Phishing Follow-Through Detected"
            desc = (
                f"Detected {count} event(s) on asset {asset_id} with "
                f"suspicious referrer URL patterns within the last "
                f"{DETECTION_WINDOW_MINUTES} minutes, indicating a "
                f"potential phishing compromise."
            )
            inc = _create_incident(db, title, desc, "Medium", asset_id)
            if inc:
                incidents.append(inc)
    return incidents


def _rule_ransomware(db: Session, cutoff: datetime) -> list[Incident]:
    """Rapid file-access/modification burst on a single asset."""
    rows = (
        db.query(Event.asset_id, func.count(Event.event_id))
        .filter(
            Event.event_type == RANSOMWARE_EVENT_TYPE,
            Event.timestamp >= cutoff,
            Event.raw_payload.contains(RANSOMWARE_PAYLOAD_MARKER),
        )
        .group_by(Event.asset_id)
        .having(func.count(Event.event_id) > THRESHOLD_RANSOMWARE_FILES)
        .all()
    )
    incidents = []
    for asset_id, cnt in rows:
        title = "Ransomware-Like Behavior Detected"
        desc = (
            f"Detected {cnt} rapid file access/modification events on asset "
            f"{asset_id} within the last {DETECTION_WINDOW_MINUTES} minutes "
            f"(threshold: {THRESHOLD_RANSOMWARE_FILES}). This pattern is "
            f"consistent with ransomware encryption activity."
        )
        inc = _create_incident(db, title, desc, "Critical", asset_id)
        if inc:
            incidents.append(inc)
    return incidents
