from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from .database import Base

class Asset(Base):
    __tablename__ = "Assets"

    asset_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # server, database, endpoint, vpn, etc.
    ip_address = Column(String, nullable=True)
    criticality = Column(String, nullable=False)  # Low, Medium, High, Critical
    owner = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    events = relationship("Event", back_populates="asset", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="asset", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="asset", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "Events"

    event_id = Column(String, primary_key=True)
    asset_id = Column(String, ForeignKey("Assets.asset_id"), nullable=True)
    source_ip = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # login_failed, port_scan, download, etc.
    raw_payload = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship to Asset
    asset = relationship("Asset", back_populates="events")


class Incident(Base):
    __tablename__ = "Incidents"

    incident_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    severity = Column(String, nullable=False)  # Low, Medium, High, Critical
    status = Column(String, default="open")     # open, investigating, contained, closed
    related_asset_id = Column(String, ForeignKey("Assets.asset_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Asset
    asset = relationship("Asset", back_populates="incidents")


class RiskScore(Base):
    __tablename__ = "RiskScores"

    score_id = Column(String, primary_key=True)
    asset_id = Column(String, ForeignKey("Assets.asset_id"), nullable=False)
    rule_score = Column(Float, nullable=False)
    ml_score = Column(Float, nullable=False)
    criticality_weight = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # Low, Medium, High, Critical
    computed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Asset
    asset = relationship("Asset", back_populates="risk_scores")


class ContainmentAction(Base):
    __tablename__ = "ContainmentActions"

    action_id = Column(String, primary_key=True)
    incident_id = Column(String, ForeignKey("Incidents.incident_id"), nullable=False)
    action_type = Column(String, nullable=False)  # block_ip, disable_user, force_mfa, reset_password, quarantine
    target = Column(String, nullable=False)
    status = Column(String, default="simulated_success")
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssetSnapshot(Base):
    __tablename__ = "AssetSnapshots"

    snapshot_id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    asset_count = Column(Integer, nullable=False)


class AssetChange(Base):
    __tablename__ = "AssetChanges"

    change_id = Column(String, primary_key=True)
    snapshot_id = Column(String, ForeignKey("AssetSnapshots.snapshot_id"), nullable=False)
    asset_id = Column(String, nullable=False)
    change_type = Column(String, nullable=False)  # added, removed, modified
    timestamp = Column(DateTime, default=datetime.utcnow)

