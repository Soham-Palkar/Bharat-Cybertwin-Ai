"""
Module 3 — Simulate Router

POST endpoints that trigger attack-shaped event bursts via the
attack_injection service.  Each endpoint accepts an optional asset_id
(defaults to a random asset) and an optional intensity parameter.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import SimulateRequest, SimulateResponse
from ..services.attack_injection import (
    inject_bruteforce,
    inject_credential_stuffing,
    inject_impossible_travel,
    inject_port_scan,
    inject_insider_threat,
    inject_exfiltration,
    inject_phishing,
    inject_privilege_escalation,
    inject_ransomware,
)

router = APIRouter(prefix="/simulate", tags=["Attack Simulation"])


def _run_injection(func, attack_type: str, req: SimulateRequest,
                   db: Session) -> SimulateResponse:
    """Shared helper that runs an injection function and builds the response."""
    try:
        target_id, events = func(db, asset_id=req.asset_id,
                                 intensity=req.intensity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SimulateResponse(
        status="success",
        attack_type=attack_type,
        target_asset_id=target_id,
        events_generated=len(events),
    )


@router.post("/bruteforce", response_model=SimulateResponse)
def simulate_bruteforce(req: SimulateRequest = SimulateRequest(),
                        db: Session = Depends(get_db)):
    return _run_injection(inject_bruteforce, "bruteforce", req, db)


@router.post("/credential-stuffing", response_model=SimulateResponse)
def simulate_credential_stuffing(req: SimulateRequest = SimulateRequest(),
                                 db: Session = Depends(get_db)):
    return _run_injection(inject_credential_stuffing, "credential-stuffing", req, db)


@router.post("/impossible-travel", response_model=SimulateResponse)
def simulate_impossible_travel(req: SimulateRequest = SimulateRequest(),
                               db: Session = Depends(get_db)):
    return _run_injection(inject_impossible_travel, "impossible-travel", req, db)


@router.post("/port-scan", response_model=SimulateResponse)
def simulate_port_scan(req: SimulateRequest = SimulateRequest(),
                       db: Session = Depends(get_db)):
    return _run_injection(inject_port_scan, "port-scan", req, db)


@router.post("/insider-threat", response_model=SimulateResponse)
def simulate_insider_threat(req: SimulateRequest = SimulateRequest(),
                            db: Session = Depends(get_db)):
    return _run_injection(inject_insider_threat, "insider-threat", req, db)


@router.post("/exfiltration", response_model=SimulateResponse)
def simulate_exfiltration(req: SimulateRequest = SimulateRequest(),
                          db: Session = Depends(get_db)):
    return _run_injection(inject_exfiltration, "exfiltration", req, db)


@router.post("/phishing", response_model=SimulateResponse)
def simulate_phishing(req: SimulateRequest = SimulateRequest(),
                      db: Session = Depends(get_db)):
    return _run_injection(inject_phishing, "phishing", req, db)


@router.post("/privilege-escalation", response_model=SimulateResponse)
def simulate_privilege_escalation(req: SimulateRequest = SimulateRequest(),
                                  db: Session = Depends(get_db)):
    return _run_injection(inject_privilege_escalation, "privilege-escalation", req, db)


@router.post("/ransomware", response_model=SimulateResponse)
def simulate_ransomware(req: SimulateRequest = SimulateRequest(),
                        db: Session = Depends(get_db)):
    return _run_injection(inject_ransomware, "ransomware", req, db)
