"""HuntGPT Gemini Service Module"""
import os
import json
from typing import List
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from ..constants import MITRE_ATTACK_MAPPING
from ..models import Asset, Incident, RiskScore, AssetSnapshot, AssetChange, ContainmentAction
from ..schemas import (
    AskHuntGPTResponse,
    MitreItem,
    AssetReference,
    IncidentReference
)


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not found!")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"

    def build_context(self, db: Session) -> str:
        """Build CyberTwin context for Gemini from database data"""
        # Get assets (limit to last 100 for token efficiency)
        assets = db.query(Asset).limit(100).all()
        assets_list = []
        for asset in assets:
            assets_list.append({
                "asset_id": asset.asset_id,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "ip_address": asset.ip_address,
                "criticality": asset.criticality,
                "owner": asset.owner
            })

        # Get risk scores (limit to last 200)
        risk_scores = db.query(RiskScore).order_by(RiskScore.computed_at.desc()).limit(200).all()
        risk_list = []
        for risk in risk_scores:
            risk_list.append({
                "asset_id": risk.asset_id,
                "rule_score": risk.rule_score,
                "ml_score": risk.ml_score,
                "total_score": risk.total_score,
                "severity": risk.severity,
                "computed_at": risk.computed_at.isoformat()
            })

        # Get incidents (last 100)
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(100).all()
        incident_list = []
        for inc in incidents:
            incident_list.append({
                "incident_id": inc.incident_id,
                "title": inc.title,
                "severity": inc.severity,
                "status": inc.status,
                "related_asset_id": inc.related_asset_id,
                "description": (inc.description[:200] + "..." if inc.description and len(inc.description) > 200 else inc.description),
                "created_at": inc.created_at.isoformat()
            })

        # Get snapshots (last 10)
        snapshots = db.query(AssetSnapshot).order_by(AssetSnapshot.uploaded_at.desc()).limit(10).all()
        snap_list = []
        for snap in snapshots:
            snap_list.append({
                "snapshot_id": snap.snapshot_id,
                "filename": snap.filename,
                "uploaded_at": snap.uploaded_at.isoformat(),
                "asset_count": snap.asset_count
            })

        # Get asset changes (last 50)
        changes = db.query(AssetChange).order_by(AssetChange.timestamp.desc()).limit(50).all()
        change_list = []
        for chg in changes:
            change_list.append({
                "change_id": chg.change_id,
                "snapshot_id": chg.snapshot_id,
                "asset_id": chg.asset_id,
                "change_type": chg.change_type,
                "timestamp": chg.timestamp.isoformat()
            })

        # Get containment history (last 20)
        containment = db.query(ContainmentAction).order_by(ContainmentAction.created_at.desc()).limit(20).all()
        containment_list = []
        for act in containment:
            containment_list.append({
                "action_id": act.action_id,
                "incident_id": act.incident_id,
                "action_type": act.action_type,
                "target": act.target,
                "status": act.status,
                "created_at": act.created_at.isoformat()
            })

        # Build context string
        context = f"""CyberTwin AI Security Data:

Assets:
{json.dumps(assets_list, indent=2)}

Risk Scores:
{json.dumps(risk_list, indent=2)}

Incidents:
{json.dumps(incident_list, indent=2)}

Asset Snapshots (Inventory Changes):
{json.dumps(snap_list, indent=2)}

Asset Changes:
{json.dumps(change_list, indent=2)}

Containment History:
{json.dumps(containment_list, indent=2)}

MITRE ATT&CK Mapping:
{json.dumps(MITRE_ATTACK_MAPPING, indent=2)}
"""
        return context

    def ask_huntgpt(self, query: str, db: Session) -> AskHuntGPTResponse:
        """Process query through Gemini, validate response, return structured answer"""
        # Build context
        context = self.build_context(db)

        # System and user prompts
        system_prompt = """You are CyberTwin SOC Copilot, an expert cybersecurity analyst.

RULES:
1. NEVER hallucinate, invent, or fabricate data about assets, incidents, users, IP addresses, risk scores, or MITRE techniques!
2. Only use the data provided in the CyberTwin context.
3. If you do NOT have sufficient evidence to answer the question, EXACTLY reply with {"answer": "Insufficient evidence available.", "mitre": [], "assets": [], "incidents": [], "recommendations": []}
4. Always respond as valid JSON, no markdown, no extra characters!
5. Your JSON must ALWAYS include all 5 fields: answer (string), mitre (array of {"id": "...", "name": "..."}), assets (array of {"asset_id": "...", "name": "...", "risk_score": ...}), incidents (array of {"incident_id": "...", "title": "..."}), recommendations (array of strings).
6. For "Generate executive report" or "CISO summary", follow this structure in "answer":
  # Executive Report
  ## Summary
  ## Threat Overview
  ## Critical Assets
  ## Infrastructure Changes
  ## Top Incidents
  ## MITRE Coverage
  ## Risk Trends
  ## Containment Recommendations
  ## Immediate Actions
7. You can answer questions about:
  - What changed after latest upload
  - Which assets were added/removed/modified
  - Compare snapshots
  - Inventory growth
  - Newly exposed devices
  - Etc.
"""
        user_prompt = f"""Context:
{context}

Question:
{query}
"""

        try:
            # Call Gemini
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,  # Low temp for determinism
                    response_mime_type="application/json"
                )
            )

            # Parse and validate
            response_text = response.text.strip()
            parsed = json.loads(response_text)

            # Validate through Pydantic (addendum requirement 5)
            validated_response = AskHuntGPTResponse(**parsed)
            return validated_response

        except Exception as e:
            print(f"Gemini error: {str(e)}")
            # Fallback response (addendum requirement 5)
            return AskHuntGPTResponse(
                answer="Insufficient evidence available.",
                mitre=[],
                assets=[],
                incidents=[],
                recommendations=[]
            )
