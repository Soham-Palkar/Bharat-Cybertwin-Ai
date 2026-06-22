from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
from sqlalchemy import desc

from ..database import get_db
from ..models import RiskScore, Asset
from ..services.risk_engine import run_risk_scan

router = APIRouter(prefix="/risk", tags=["Risk Scores"])


@router.get("")
def get_risk_scores(db: Session = Depends(get_db)):
    """
    Get latest risk scores for all assets (sorted by total_score descending).
    Automatically runs a fresh risk scan on every request.
    """
    # Run a fresh risk scan first
    run_risk_scan(db)

    # Get latest score per asset (using subquery to find max computed_at)
    from sqlalchemy import func, tuple_

    subq = (
        db.query(
            RiskScore.asset_id,
            func.max(RiskScore.computed_at).label("max_computed")
        )
        .group_by(RiskScore.asset_id)
        .subquery()
    )

    latest_scores = (
        db.query(RiskScore, Asset)
        .join(subq, (RiskScore.asset_id == subq.c.asset_id) & (RiskScore.computed_at == subq.c.max_computed))
        .join(Asset, RiskScore.asset_id == Asset.asset_id)
        .order_by(desc(RiskScore.total_score))
        .all()
    )

    return {
        "asset_count": len(latest_scores),
        "assets": [
            {
                "asset_id": score.asset_id,
                "asset_name": asset.name,
                "asset_criticality": asset.criticality,
                "rule_score": score.rule_score,
                "ml_score": score.ml_score,
                "criticality_weight": score.criticality_weight,
                "total_score": score.total_score,
                "severity": score.severity,
                "computed_at": score.computed_at.isoformat() if score.computed_at else None
            }
            for score, asset in latest_scores
        ]
    }


@router.post("/scan")
def run_risk_scan_endpoint(db: Session = Depends(get_db)):
    """Manually trigger a risk scan (and ML scan)."""
    scores = run_risk_scan(db)
    return {"status": "success", "score_count": len(scores)}
