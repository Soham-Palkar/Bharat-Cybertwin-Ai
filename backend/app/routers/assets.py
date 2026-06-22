import csv
import uuid
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter()


def asset_to_dict(asset: models.Asset) -> Dict:
    return {
        "name": asset.name,
        "asset_type": asset.asset_type,
        "ip_address": asset.ip_address,
        "criticality": asset.criticality,
        "owner": asset.owner
    }


def compare_assets(old: Dict, new: Dict) -> bool:
    return (old["name"] != new["name"] or
            old["asset_type"] != new["asset_type"] or
            old["ip_address"] != new["ip_address"] or
            old["criticality"] != new["criticality"] or
            old["owner"] != new["owner"])


@router.post("/upload-assets", response_model=schemas.UploadResponse)
async def upload_assets(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    assets_incoming = []
    filename = "upload.json"

    # Step 1: Parse input
    if "application/json" in content_type:
        try:
            body = await request.json()
            upload_req = schemas.AssetUploadRequest(**body)
            assets_incoming = upload_req.assets
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")

    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
            file = form.get("file")
            if not file or not isinstance(file, StarletteUploadFile):
                raise HTTPException(status_code=400, detail="Missing CSV file in 'file' field")
            filename = file.filename or "upload.csv"

            contents = await file.read()
            decoded = contents.decode("utf-8-sig").splitlines()
            reader = csv.DictReader(decoded)

            if not reader.fieldnames:
                raise HTTPException(status_code=400, detail="CSV file is empty or has no headers")

            # Match fields case-insensitively
            name_col = None
            type_col = None
            crit_col = None
            ip_col = None
            owner_col = None

            for original in reader.fieldnames:
                normalized = original.strip().lower()
                if normalized == "name":
                    name_col = original
                elif normalized in ("asset_type", "type"):
                    type_col = original
                elif normalized in ("criticality", "critical"):
                    crit_col = original
                elif normalized in ("ip_address", "ip", "ipaddress"):
                    ip_col = original
                elif normalized == "owner":
                    owner_col = original

            if not name_col or not type_col or not crit_col:
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain headers: 'name', 'asset_type' (or 'type'), and 'criticality' (or 'critical')"
                )

            for idx, row in enumerate(reader, start=1):
                name_val = row.get(name_col)
                type_val = row.get(type_col)
                crit_val = row.get(crit_col)

                if not name_val or not name_val.strip():
                    raise HTTPException(status_code=400, detail=f"Row {idx} is missing required field 'name'")
                if not type_val or not type_val.strip():
                    raise HTTPException(status_code=400, detail=f"Row {idx} is missing required field 'asset_type'")
                if not crit_val or not crit_val.strip():
                    raise HTTPException(status_code=400, detail=f"Row {idx} is missing required field 'criticality'")

                crit_val_clean = crit_val.strip().title()
                if crit_val_clean not in {"Low", "Medium", "High", "Critical"}:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Row {idx} has invalid criticality '{crit_val}'. Must be Low, Medium, High, or Critical"
                    )

                assets_incoming.append(
                    schemas.AssetCreate(
                        name=name_val.strip(),
                        asset_type=type_val.strip(),
                        ip_address=row.get(ip_col).strip() if ip_col and row.get(ip_col) else None,
                        criticality=crit_val_clean,
                        owner=row.get(owner_col).strip() if owner_col and row.get(owner_col) else None
                    )
                )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Content-Type must be application/json or multipart/form-data")

    if not assets_incoming:
        raise HTTPException(status_code=400, detail="No assets found to import")

    # Step 2: Get current assets (previous snapshot)
    current_assets = db.query(models.Asset).all()
    current_assets_by_name = {a.name: a for a in current_assets}

    # Step 3: Create new snapshot
    snapshot_id = f"SNAP-{str(uuid.uuid4())[:8].upper()}"
    snapshot = models.AssetSnapshot(
        snapshot_id=snapshot_id,
        filename=filename,
        asset_count=len(assets_incoming)
    )
    db.add(snapshot)

    # Step 4: Compute diff
    changes: List[models.AssetChange] = []
    incoming_names = {a.name for a in assets_incoming}
    existing_names = set(current_assets_by_name.keys())

    # Generate sequential asset IDs: AST-1001, AST-1002, etc.
    count = db.query(func.count(models.Asset.asset_id)).scalar()
    next_index = 1001 + count

    for asset_data in assets_incoming:
        if asset_data.name in current_assets_by_name:
            # Check for modification
            existing_asset = current_assets_by_name[asset_data.name]
            old_data = asset_to_dict(existing_asset)
            new_data = {
                "name": asset_data.name,
                "asset_type": asset_data.asset_type,
                "ip_address": asset_data.ip_address,
                "criticality": asset_data.criticality,
                "owner": asset_data.owner
            }
            if compare_assets(old_data, new_data):
                # Update existing asset
                existing_asset.asset_type = asset_data.asset_type
                existing_asset.ip_address = asset_data.ip_address
                existing_asset.criticality = asset_data.criticality
                existing_asset.owner = asset_data.owner
                changes.append(models.AssetChange(
                    change_id=f"CHG-{str(uuid.uuid4())[:8].upper()}",
                    snapshot_id=snapshot_id,
                    asset_id=existing_asset.asset_id,
                    change_type="modified"
                ))
        else:
            # Add new asset
            asset_id = f"AST-{next_index}"
            next_index += 1
            new_asset = models.Asset(
                asset_id=asset_id,
                name=asset_data.name,
                asset_type=asset_data.asset_type,
                ip_address=asset_data.ip_address,
                criticality=asset_data.criticality,
                owner=asset_data.owner
            )
            db.add(new_asset)
            changes.append(models.AssetChange(
                change_id=f"CHG-{str(uuid.uuid4())[:8].upper()}",
                snapshot_id=snapshot_id,
                asset_id=asset_id,
                change_type="added"
            ))

    # Mark removed assets
    for name in existing_names - incoming_names:
        asset = current_assets_by_name[name]
        changes.append(models.AssetChange(
            change_id=f"CHG-{str(uuid.uuid4())[:8].upper()}",
            snapshot_id=snapshot_id,
            asset_id=asset.asset_id,
            change_type="removed"
        ))
        # Remove from DB
        db.delete(asset)

    # Add all changes
    for chg in changes:
        db.add(chg)

    # Commit
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")

    return schemas.UploadResponse(
        status="success",
        snapshot_id=snapshot_id,
        changes=[schemas.AssetChangeResponse.model_validate(c) for c in changes],
        note="Upload processed; changes recorded"
    )


@router.get("/assets", response_model=List[schemas.AssetResponse])
def get_assets(db: Session = Depends(get_db)):
    crit_order = case(
        (models.Asset.criticality == "Critical", 1),
        (models.Asset.criticality == "High", 2),
        (models.Asset.criticality == "Medium", 3),
        (models.Asset.criticality == "Low", 4),
        else_=5
    )
    assets = db.query(models.Asset).order_by(crit_order, models.Asset.name).all()
    return assets


@router.get("/infrastructure-changes", response_model=schemas.InfrastructureChangesResponse)
def get_infrastructure_changes(db: Session = Depends(get_db)):
    # Get latest snapshot
    latest_snapshot = db.query(models.AssetSnapshot).order_by(models.AssetSnapshot.uploaded_at.desc()).first()
    if not latest_snapshot:
        return schemas.InfrastructureChangesResponse(
            added=0,
            removed=0,
            modified=0,
            latest_snapshot=None
        )

    # Get changes from latest snapshot
    changes = db.query(models.AssetChange).filter(
        models.AssetChange.snapshot_id == latest_snapshot.snapshot_id
    ).all()
    added = sum(1 for c in changes if c.change_type == "added")
    removed = sum(1 for c in changes if c.change_type == "removed")
    modified = sum(1 for c in changes if c.change_type == "modified")

    return schemas.InfrastructureChangesResponse(
        added=added,
        removed=removed,
        modified=modified,
        latest_snapshot=schemas.SnapshotResponse.model_validate(latest_snapshot)
    )


@router.get("/snapshots", response_model=List[schemas.SnapshotResponse])
def get_snapshots(db: Session = Depends(get_db)):
    snapshots = db.query(models.AssetSnapshot).order_by(
        models.AssetSnapshot.uploaded_at.desc()
    ).all()
    return [schemas.SnapshotResponse.model_validate(s) for s in snapshots]


@router.get("/snapshots/{snapshot_id}/changes", response_model=List[schemas.AssetChangeResponse])
def get_snapshot_changes(snapshot_id: str, db: Session = Depends(get_db)):
    changes = db.query(models.AssetChange).filter(
        models.AssetChange.snapshot_id == snapshot_id
    ).order_by(models.AssetChange.timestamp.desc()).all()
    return [schemas.AssetChangeResponse.model_validate(c) for c in changes]
