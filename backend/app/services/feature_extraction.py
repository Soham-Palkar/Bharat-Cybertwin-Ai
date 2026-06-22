"""
Module 5 — Feature Extraction

Extracts 7 features per asset from Events within the detection window:
1. failed_login_count
2. download_count
3. session_duration_seconds (uses max time span between first and last event)
4. bytes_transferred_total
5. distinct_port_count
6. geo_location_change_count
7. admin_action_count
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Event
from .detection import DETECTION_WINDOW_MINUTES


def extract_features(db: Session) -> Dict[str, Dict[str, float]]:
    """
    Extract feature vectors for all assets that have at least one event in the
    last DETECTION_WINDOW_MINUTES minutes.

    Returns: dict[asset_id, feature_dict]
    """
    cutoff = datetime.utcnow() - timedelta(minutes=DETECTION_WINDOW_MINUTES)

    # Get all relevant events
    events = (
        db.query(Event)
        .filter(Event.timestamp >= cutoff, Event.asset_id.isnot(None))
        .order_by(Event.timestamp)
        .all()
    )

    # Group events by asset
    asset_events: Dict[str, List[Event]] = {}
    for evt in events:
        asset_events.setdefault(evt.asset_id, []).append(evt)

    # Extract features for each asset
    features_by_asset: Dict[str, Dict[str, float]] = {}
    for asset_id, evts in asset_events.items():
        features = _extract_single_asset_features(evts)
        features_by_asset[asset_id] = features

    return features_by_asset


def _extract_single_asset_features(events: List[Event]) -> Dict[str, float]:
    """Extract the 7 features for a single asset's list of events."""
    failed_login_count = 0
    download_count = 0
    bytes_transferred = 0
    distinct_ports = set()
    admin_action_count = 0
    geo_locations = set()

    # Track timestamps for session duration
    timestamps = []

    for evt in events:
        timestamps.append(evt.timestamp)

        if evt.event_type == "login_failed":
            failed_login_count += 1
        elif evt.event_type == "download":
            download_count += 1
        elif evt.event_type == "data_transfer":
            # Extract bytes from raw_payload
            if evt.raw_payload:
                m = re.search(r"(\d+) bytes", evt.raw_payload)
                if m:
                    bytes_transferred += int(m.group(1))
        elif evt.event_type == "port_scan":
            # Extract port from raw_payload (if any)
            if evt.raw_payload:
                m = re.search(r"port (\d+)", evt.raw_payload)
                if m:
                    distinct_ports.add(int(m.group(1)))
        elif evt.event_type == "admin_action":
            admin_action_count += 1

        # Extract geo from payload for any event
        if evt.raw_payload:
            m = re.search(r"\[geo: ([^\]]+)\]", evt.raw_payload)
            if m:
                geo_locations.add(m.group(1))

    # Calculate session duration (max time span)
    session_duration = 0.0
    if len(timestamps) >= 2:
        session_duration = (max(timestamps) - min(timestamps)).total_seconds()

    # Geo change count is (number of distinct locations - 1) if > 1, else 0
    geo_change_count = max(0, len(geo_locations) - 1)

    return {
        "failed_login_count": float(failed_login_count),
        "download_count": float(download_count),
        "session_duration_seconds": session_duration,
        "bytes_transferred_total": float(bytes_transferred),
        "distinct_port_count": float(len(distinct_ports)),
        "geo_location_change_count": float(geo_change_count),
        "admin_action_count": float(admin_action_count),
    }


# List of feature names in fixed order (for ML model input)
FEATURE_NAMES = [
    "failed_login_count",
    "download_count",
    "session_duration_seconds",
    "bytes_transferred_total",
    "distinct_port_count",
    "geo_location_change_count",
    "admin_action_count",
]
