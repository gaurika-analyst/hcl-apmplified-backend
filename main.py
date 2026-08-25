import sys
import os
from contextlib import asynccontextmanager

# Add backend directory to sys.path for direct imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas import (
    Career, Skill, AssessmentStartRequest, AssessmentStartResponse,
    AssessmentSubmitRequest, AssessmentResultResponse, SkillGapsResponse,
    LearningPathResponse, SessionState, ChatRequest, ChatResponse,
    FeedbackRequest, SelectCareerRequest
)
from state.session_store import get_session_store
from services.career_service import get_career_service
from services.skill_gap_engine import get_skill_gap_engine
from agents.orchestrator import get_orchestrator
from db.vector_store import get_vector_store
from auth.dependencies import get_current_user, verify_session_ownership, AuthenticatedUser
from auth.firebase import initialize_firebase

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safely initialize Firebase Admin SDK on application startup
    initialize_firebase()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend for AI Personalized Career Recommendation & Learning Path System (Firebase Authenticated)",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store = get_session_store()
career_service = get_career_service()
skill_gap_engine = get_skill_gap_engine()
orchestrator = get_orchestrator()
vector_store = get_vector_store()

# --- PUBLIC ENDPOINTS ---

@app.get("/careers", response_model=List[Career])
def list_careers():
    """Lists all supported technical careers."""
    return career_service.get_all_careers()

@app.get("/careers/{career_id}", response_model=Career)
def get_career(career_id: str):
    """Retrieves details for a specific career."""
    career = career_service.get_career_by_id(career_id)
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Career '{career_id}' not found."
        )
    return career

@app.post("/courses/seed", response_model=List[Dict[str, Any]])
def reseed_courses():
    """Inspects or reloads seed course catalog."""
    return vector_store.get_all_courses()

# --- PROTECTED / AUTHENTICATED ENDPOINTS ---

@app.post("/session/start", response_model=SessionState)
def start_session(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Creates or retrieves the existing application session for the authenticated Firebase user.
    Uses current_user.uid as the stable learner_id.
    """
    session = session_store.get_or_create_session(learner_id=current_user.uid)
    return session

@app.post("/session/{session_id}/career", response_model=SessionState)
def select_career(
    session_id: str,
    payload: SelectCareerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Selects a target career for the specified session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    try:
        updated_session = orchestrator.handle_select_career(session, payload.career_id)
        session_store.save_session(updated_session)
        return updated_session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/assessment/start", response_model=AssessmentStartResponse)
def start_assessment(
    session_id: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Starts a career-specific skill assessment for the session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    if not session.selected_career:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No career selected for this session. Call POST /session/{id}/career first."
        )
    try:
        updated_session = orchestrator.handle_start_assessment(session)
        session_store.save_session(updated_session)
        
        assessment_data = updated_session.assessment
        return AssessmentStartResponse(
            assessment_id=assessment_data["assessment_id"],
            career_id=assessment_data["career_id"],
            career_name=assessment_data["career_name"],
            questions=assessment_data["questions"],
            total_questions=assessment_data["total_questions"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/assessment/{assessment_id}/submit", response_model=AssessmentResultResponse)
def submit_assessment(
    assessment_id: str,
    payload: AssessmentSubmitRequest,
    session_id: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Submits assessment answers, evaluates score & skill gaps, and generates learning path."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    if not session.assessment or session.assessment.get("assessment_id") != assessment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assessment ID '{assessment_id}' does not match active session assessment."
        )
    try:
        updated_session = orchestrator.handle_submit_assessment(session, payload.answers)
        session_store.save_session(updated_session)
        return updated_session.assessment_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/session/{session_id}/assessment/result", response_model=AssessmentResultResponse)
def get_assessment_result(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves assessment results for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    if not session.assessment_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment has not been completed for this session."
        )
    return session.assessment_result

@app.get("/session/{session_id}/skills", response_model=SkillGapsResponse)
def get_session_skills(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves skill gap analysis for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    if not session.selected_career:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No career selected for this session."
        )

    gaps = skill_gap_engine.compute_skill_gaps(
        career=session.selected_career,
        assessment_result=session.assessment_result,
        profile_skills_0_5=session.learner_profile.current_skills
    )
    return gaps

@app.get("/session/{session_id}/path", response_model=LearningPathResponse)
def get_learning_path(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves ordered stairs-ready learning path for the session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    if not session.selected_career:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No career selected for this session."
        )

    updated_session = orchestrator.handle_get_path(session)
    session_store.save_session(updated_session)

    readiness = updated_session.assessment_result.readiness if updated_session.assessment_result else "Developing"

    return LearningPathResponse(
        learner_id=updated_session.learner_id,
        career_id=updated_session.selected_career.id,
        career_name=updated_session.selected_career.name,
        overall_readiness=readiness,
        learning_path=updated_session.learning_path
    )

@app.post("/chat", response_model=ChatResponse)
def chat_with_agent(
    payload: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Interacts with the AI Career Recommendation Assistant."""
    session = session_store.get_session(payload.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{payload.session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    reply_text = orchestrator.handle_chat(session, payload.message)
    session_store.save_session(session)

    return ChatResponse(
        session_id=session.session_id,
        response=reply_text,
        agent_trace=session.agent_trace
    )

@app.post("/session/{session_id}/feedback", response_model=SessionState)
def log_feedback(
    session_id: str,
    payload: FeedbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Logs user feedback for a learning path milestone."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    updated_session = orchestrator.handle_feedback(
        session, payload.milestone_order, payload.rating, payload.feedback_text
    )
    session_store.save_session(updated_session)
    return updated_session

@app.get("/session/{session_id}/trace", response_model=List[Dict[str, Any]])
def get_agent_trace(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves complete agent execution trace logs."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    verify_session_ownership(session.learner_id, current_user)

    return session.agent_trace
