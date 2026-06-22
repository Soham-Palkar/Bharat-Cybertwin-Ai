from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List

from ..database import get_db
from ..services.ml_engine import run_ml_scan
from ..services.feature_extraction import extract_features

router = APIRouter(prefix="/ml", tags=["ML Anomaly Detection"])


@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    """
    Get current ML anomaly scores for all assets with events in the detection window.
    Returns sorted by threat_confidence descending.
    """
    ml_scores = run_ml_scan(db)
    sorted_assets = sorted(
        ml_scores.items(),
        key=lambda x: x[1]["threat_confidence"],
        reverse=True
    )
    return {
        "asset_count": len(sorted_assets),
        "assets": [
            {"asset_id": aid, **scores}
            for aid, scores in sorted_assets
        ]
    }


@router.get("/features")
def get_features(db: Session = Depends(get_db)):
    """Get extracted feature vectors for debugging/inspection."""
    features = extract_features(db)
    return {
        "asset_count": len(features),
        "assets": [{"asset_id": aid, **feats} for aid, feats in features.items()]
    }
