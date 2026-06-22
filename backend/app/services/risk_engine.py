"""
Module 6 — Risk Engine

Calculates total risk score as:
Risk Score = Rule Score + ML Score + Asset Criticality Weight

Scores each asset and saves to RiskScores table.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Asset, Incident, RiskScore
from .ml_engine import run_ml_scan

logger = logging.getLogger("cybertwin.risk")

# ===================================================================
# TUNEABLE THRESHOLDS & MAPPINGS
# ===================================================================

SEVERITY_TO_RULE_SCORE = {
    "Low": 10,
    "Medium": 20,
    "High": 30,
    "Critical": 40,
}
"""Maps incident severity to rule score contribution (uses max of open incidents)."""

CRITICALITY_TO_WEIGHT = {
    "Low": 5,
    "Medium": 10,
    "High": 15,
    "Critical": 20,
}
"""Maps asset criticality to criticality weight."""

RISK_SCORE_TO_SEVERITY = [
    (0, 30, "Low"),
    (30, 60, "Medium"),
    (60, 85, "High"),
    (85, float("inf"), "Critical"),
]
"""Maps total risk score to severity band (lower bound inclusive, upper bound exclusive)."""

# ===================================================================
# CORE RISK CALCULATION
# ===================================================================


def run_risk_scan(db: Session) -> List[RiskScore]:
    """
    Run full risk scan:
    1. Get ML scores from ml_engine
    2. Calculate rule scores from open incidents
    3. Calculate criticality weights
    4. Combine into total risk score (ml_score rescaled to 0-20)
    5. Save to RiskScores table
    6. Return list of new RiskScore objects
    """
    ml_scores = run_ml_scan(db)
    assets = db.query(Asset).all()

    new_scores: List[RiskScore] = []

    for asset in assets:
        rule_score = _calculate_rule_score(db, asset.asset_id)
        raw_ml_score = ml_scores.get(asset.asset_id, {}).get("threat_confidence", 0.0)
        ml_score = raw_ml_score / 5.0  # Rescale from 0-100 to 0-20
        criticality_weight = CRITICALITY_TO_WEIGHT.get(asset.criticality, 10)
        total_score = rule_score + ml_score + criticality_weight
        severity = _map_score_to_severity(total_score)

        score_obj = RiskScore(
            score_id=f"SCR-{uuid.uuid4().hex[:8].upper()}",
            asset_id=asset.asset_id,
            rule_score=rule_score,
            ml_score=ml_score,
            criticality_weight=criticality_weight,
            total_score=total_score,
            severity=severity,
            computed_at=datetime.utcnow(),
        )
        db.add(score_obj)
        new_scores.append(score_obj)

    db.commit()
    logger.info("Risk scan completed, saved %d risk scores.", len(new_scores))
    return new_scores


def _calculate_rule_score(db: Session, asset_id: str) -> float:
    """
    Calculate rule score for an asset: max of SEVERITY_TO_RULE_SCORE for all open incidents
    (0 if no open incidents).
    """
    open_incidents = (
        db.query(Incident)
        .filter(Incident.related_asset_id == asset_id, Incident.status == "open")
        .all()
    )
    if not open_incidents:
        return 0.0

    max_score = 0.0
    for inc in open_incidents:
        s = SEVERITY_TO_RULE_SCORE.get(inc.severity, 10)
        if s > max_score:
            max_score = s
    return max_score


def _map_score_to_severity(score: float) -> str:
    """Map total risk score to severity band."""
    for lower, upper, sev in RISK_SCORE_TO_SEVERITY:
        if lower <= score < upper:
            return sev
    return "Low"
