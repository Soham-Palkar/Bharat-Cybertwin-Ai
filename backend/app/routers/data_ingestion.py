import csv
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.post("/upload-events", response_model=schemas.UploadResponse)
async def upload_events(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    events_to_create = []
    filename = "events.json"

    if "application/json" in content_type:
        try:
            body = await request.json()
            upload_req = schemas.EventUploadRequest(**body)
            events_to_create = upload_req.events
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")
    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
            file = form.get("file")
            if not file or not isinstance(file, StarletteUploadFile):
                raise HTTPException(status_code=400, detail="Missing CSV file in 'file' field")
            filename = file.filename or "events.csv"

            contents = await file.read()
            decoded = contents.decode("utf-8-sig").splitlines()
            reader = csv.DictReader(decoded)

            for idx, row in enumerate(reader, start=1):
                event_type = row.get("event_type", row.get("type", "unknown"))
                if not event_type or not event_type.strip():
                    raise HTTPException(status_code=400, detail=f"Row {idx} missing 'event_type'")
                ts_str = row.get("timestamp", row.get("time", None))
                timestamp = None
                if ts_str:
                    try:
                        timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass  # default to now if parsing fails
                events_to_create.append(
                    schemas.EventCreate(
                        asset_id=row.get("asset_id", row.get("asset")),
                        source_ip=row.get("source_ip", row.get("src_ip", row.get("ip"))),
                        event_type=event_type.strip(),
                        raw_payload=row.get("raw_payload", row.get("payload", row.get("message"))),
                        timestamp=timestamp
                    )
                )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Content-Type must be application/json or multipart/form-data")

    if not events_to_create:
        raise HTTPException(status_code=400, detail="No events to upload")

    for ev_data in events_to_create:
        event = models.Event(
            event_id=f"EVT-{str(uuid.uuid4())[:8].upper()}",
            asset_id=ev_data.asset_id,
            source_ip=ev_data.source_ip,
            event_type=ev_data.event_type,
            raw_payload=ev_data.raw_payload,
            timestamp=ev_data.timestamp or datetime.utcnow()
        )
        db.add(event)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    return schemas.UploadResponse(
        status="success",
        note=f"Uploaded {len(events_to_create)} events"
    )


@router.post("/upload-dataset", response_model=schemas.UploadResponse)
async def upload_dataset(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    filename = "dataset.csv"

    if "multipart/form-data" not in content_type:
        raise HTTPException(status_code=400, detail="Please upload a CSV file as multipart/form-data")

    try:
        form = await request.form()
        file = form.get("file")
        if not file or not isinstance(file, StarletteUploadFile):
            raise HTTPException(status_code=400, detail="Missing CSV file in 'file' field")
        filename = file.filename or "dataset.csv"
        # We'll just store that a dataset was uploaded; actual parsing for specific formats (CICIDS etc.)
        # can be added later. For now, treat as a placeholder.
        return schemas.UploadResponse(
            status="success",
            note=f"Dataset '{filename}' received (parsing for CICIDS/UNSW-NB15 coming soon)"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process dataset: {str(e)}")
