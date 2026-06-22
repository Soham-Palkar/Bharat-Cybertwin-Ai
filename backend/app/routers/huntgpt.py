"""HuntGPT Router - Module 9"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import AskHuntGPTRequest, AskHuntGPTResponse
from ..services.gemini_service import GeminiService


router = APIRouter(prefix="", tags=["huntgpt"])
gemini_service = GeminiService()


@router.post("/ask", response_model=AskHuntGPTResponse)
def ask_huntgpt(request: AskHuntGPTRequest, db: Session = Depends(get_db)):
    """Ask HuntGPT a question about CyberTwin AI data"""
    return gemini_service.ask_huntgpt(request.query, db)
