"""
Module 4 — Incidents Router

GET  /incidents            — list incidents with optional ?status= and ?severity= filters
POST /detect/run-now       — trigger an immediate detection scan
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Incident
from ..schemas import DetectionRunResponse, IncidentResponse
from ..services.detection import run_detection_scan

router = APIRouter(tags=["Detection & Incidents"])


@router.get("/incidents", response_model=List[IncidentResponse])
def get_incidents(
    status: Optional[str] = Query(None, description="Filter by status (open, investigating, contained, closed)"),
    severity: Optional[str] = Query(None, description="Filter by severity (Low, Medium, High, Critical)"),
    db: Session = Depends(get_db),
):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    query = query.order_by(Incident.created_at.desc())
    return query.all()


@router.post("/detect/run-now", response_model=DetectionRunResponse)
def detect_run_now(db: Session = Depends(get_db)):
    """Trigger an immediate detection scan and return newly created incidents."""
    new_incidents = run_detection_scan(db)
    return DetectionRunResponse(
        status="completed",
        incidents_created=len(new_incidents),
        incidents=[IncidentResponse.model_validate(inc) for inc in new_incidents],
    )
