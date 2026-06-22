"""
Module 5 — ML Engine (Isolation Forest)

Uses scikit-learn's IsolationForest to score assets based on their feature
vectors. Fits fresh on each scan (no persistent model) with contamination=0.1.
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from .feature_extraction import extract_features, FEATURE_NAMES

logger = logging.getLogger("cybertwin.ml")

# ===================================================================
# TUNEABLE THRESHOLDS
# ===================================================================

CONTAMINATION = 0.1
"""Expected proportion of anomalies in the dataset (0.0 to 0.5)."""

# ===================================================================
# CORE ML SCORING
# ===================================================================


def run_ml_scan(db: Session) -> Dict[str, Dict[str, float]]:
    """
    Run ML anomaly detection on current feature vectors.

    Returns: dict[asset_id, {
        "anomaly_score": float,  # raw score from IsolationForest
        "threat_confidence": float,  # 0-100 normalized score
        "threat_probability": float  # 0-1 normalized probability
    }]
    """
    features_by_asset = extract_features(db)

    if not features_by_asset:
        logger.debug("No assets with events to score.")
        return {}

    # Prepare data
    asset_ids = list(features_by_asset.keys())
    X = np.array([
        [features_by_asset[aid][fname] for fname in FEATURE_NAMES]
        for aid in asset_ids
    ])

    # Fit and predict
    model = IsolationForest(contamination=CONTAMINATION, random_state=42)
    model.fit(X)

    # Get scores: decision_function returns higher for normal, lower for anomalies
    anomaly_scores = model.decision_function(X)

    # Normalize to 0-100 confidence (higher = more anomalous)
    # First, invert the score because IsolationForest gives lower = more anomalous
    min_score = np.min(anomaly_scores)
    max_score = np.max(anomaly_scores)
    if max_score - min_score > 1e-9:
        normalized = 100 * (1 - (anomaly_scores - min_score) / (max_score - min_score))
    else:
        normalized = np.full_like(anomaly_scores, 50.0)

    threat_prob = normalized / 100.0

    # Package results
    results = {}
    for i, aid in enumerate(asset_ids):
        results[aid] = {
            "anomaly_score": float(anomaly_scores[i]),
            "threat_confidence": float(normalized[i]),
            "threat_probability": float(threat_prob[i]),
        }

    logger.info("ML scan completed, scored %d assets.", len(results))
    return results
