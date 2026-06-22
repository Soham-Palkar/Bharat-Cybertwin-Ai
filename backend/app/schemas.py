from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    ip_address: Optional[str] = None
    criticality: str
    owner: Optional[str] = None

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, v: str) -> str:
        valid_criticalities = {"Low", "Medium", "High", "Critical"}
        if not v:
            raise ValueError("criticality cannot be empty")
        v_title = v.strip().title()
        if v_title not in valid_criticalities:
            raise ValueError(f"criticality must be one of {valid_criticalities}")
        return v_title

class AssetResponse(BaseModel):
    asset_id: str
    name: str
    asset_type: str
    ip_address: Optional[str] = None
    criticality: str
    owner: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssetUploadRequest(BaseModel):
    assets: List[AssetCreate]

class AssetUploadResponse(BaseModel):
    status: str
    imported: int
    asset_ids: List[str]

class EventResponse(BaseModel):
    event_id: str
    asset_id: Optional[str] = None
    source_ip: Optional[str] = None
    event_type: str
    raw_payload: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Module 3 & 4 Schemas ---

class SimulateRequest(BaseModel):
    asset_id: Optional[str] = None
    intensity: Optional[int] = None  # Optional multiplier for event count

class SimulateResponse(BaseModel):
    status: str
    attack_type: str
    target_asset_id: str
    events_generated: int

class IncidentResponse(BaseModel):
    incident_id: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    related_asset_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionRunResponse(BaseModel):
    status: str
    incidents_created: int
    incidents: List[IncidentResponse]


# --- Module 5 & 6 Schemas ---
class MlAnomalyAsset(BaseModel):
    asset_id: str
    anomaly_score: float
    threat_confidence: float
    threat_probability: float


class MlAnomaliesResponse(BaseModel):
    asset_count: int
    assets: List[MlAnomalyAsset]


class RiskScoreResponse(BaseModel):
    score_id: str
    asset_id: str
    asset_name: str
    asset_criticality: str
    rule_score: float
    ml_score: float
    criticality_weight: float
    total_score: float
    severity: str
    computed_at: datetime

    class Config:
        from_attributes = True


class RiskResponse(BaseModel):
    asset_count: int
    assets: List[RiskScoreResponse]


# --- Module 9 (HuntGPT) Schemas ---
class MitreItem(BaseModel):
    id: str
    name: str


class AssetReference(BaseModel):
    asset_id: str
    name: str
    risk_score: Optional[float] = None


class IncidentReference(BaseModel):
    incident_id: str
    title: str


class AskHuntGPTRequest(BaseModel):
    query: str = Field(..., min_length=1)


class AskHuntGPTResponse(BaseModel):
    answer: str
    mitre: List[MitreItem]
    assets: List[AssetReference]
    incidents: List[IncidentReference]
    recommendations: List[str]


# --- Module 10 (Containment) Schemas ---
class ContainRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)
    action_type: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class ContainResponse(BaseModel):
    status: str
    action_id: str
    note: str


class ContainmentActionResponse(BaseModel):
    action_id: str
    incident_id: str
    action_type: str
    target: str
    status: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContainmentHistoryResponse(BaseModel):
    actions: List[ContainmentActionResponse]


# --- Data Ingestion Schemas ---
class EventCreate(BaseModel):
    asset_id: Optional[str] = None
    source_ip: Optional[str] = None
    event_type: str
    raw_payload: Optional[str] = None
    timestamp: Optional[datetime] = None


class EventUploadRequest(BaseModel):
    events: List[EventCreate]


class EventResponse(BaseModel):
    event_id: str
    asset_id: Optional[str] = None
    source_ip: Optional[str] = None
    event_type: str
    raw_payload: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    snapshot_id: str
    filename: str
    uploaded_at: datetime
    asset_count: int

    class Config:
        from_attributes = True


class AssetChangeResponse(BaseModel):
    change_id: str
    snapshot_id: str
    asset_id: str
    change_type: str
    timestamp: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    status: str
    snapshot_id: Optional[str] = None
    changes: List[AssetChangeResponse] = []
    note: Optional[str] = None


class InfrastructureChangesResponse(BaseModel):
    added: int
    removed: int
    modified: int
    latest_snapshot: Optional[SnapshotResponse] = None

