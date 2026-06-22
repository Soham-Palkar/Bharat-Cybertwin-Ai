"""Containment Center Router - Module 10"""
import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ContainmentAction, Incident
from ..schemas import (
    ContainRequest,
    ContainResponse,
    ContainmentHistoryResponse,
    ContainmentActionResponse
)
from ..constants import CONTAINMENT_ACTION_TYPES
from ..services.containment_service import execute_real_containment
from .logs import manager


router = APIRouter(prefix="", tags=["containment"])


@router.post("/contain", response_model=ContainResponse)
async def contain(request: ContainRequest, db: Session = Depends(get_db)):
    """Simulate a containment action with real-time updates"""
    if request.action_type not in CONTAINMENT_ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action type, must be one of {CONTAINMENT_ACTION_TYPES}"
        )

    action_id = f"ACT-{str(uuid.uuid4())[:8].upper()}"

    # Step 1: Create "pending" action and send event
    pending_action = ContainmentAction(
        action_id=action_id,
        incident_id=request.incident_id,
        action_type=request.action_type,
        target=request.target,
        status="pending"
    )
    db.add(pending_action)
    db.commit()
    db.refresh(pending_action)

    await manager.broadcast({
        "type": "containment_update",
        "data": ContainmentActionResponse.model_validate(pending_action).model_dump()
    })

    # Step 2: Simulate "executing" status with delay
    await asyncio.sleep(0.8)
    pending_action.status = "executing"
    db.commit()
    db.refresh(pending_action)

    await manager.broadcast({
        "type": "containment_update",
        "data": ContainmentActionResponse.model_validate(pending_action).model_dump()
    })

    # Step 3: Execute real containment (if enabled)
    success, note = execute_real_containment(request.action_type, request.target)
    await asyncio.sleep(1.5)

    # Update action to "simulated_success" or "failed" and save note
    pending_action.status = "simulated_success" if success else "failed"
    pending_action.note = note
    db.commit()
    db.refresh(pending_action)

    # Mark incident as contained if it's not closed already
    incident = db.query(Incident).filter(Incident.incident_id == request.incident_id).first()
    if incident and incident.status != "closed":
        incident.status = "contained"
        db.commit()

        await manager.broadcast({
            "type": "incident_update",
            "data": {
                "incident_id": incident.incident_id,
                "status": "contained"
            }
        })

    # Send final containment update
    await manager.broadcast({
        "type": "containment_update",
        "data": ContainmentActionResponse.model_validate(pending_action).model_dump()
    })

    return ContainResponse(
        status="simulated_success",
        action_id=action_id,
        note="This is a simulated action - no real infrastructure was affected."
    )


@router.get("/containment-history", response_model=ContainmentHistoryResponse)
def get_containment_history(db: Session = Depends(get_db)):
    """Get all containment actions history"""
    actions = db.query(ContainmentAction).order_by(ContainmentAction.created_at.desc()).all()
    return ContainmentHistoryResponse(
        actions=[ContainmentActionResponse.model_validate(a) for a in actions]
    )
