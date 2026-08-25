from datetime import datetime, timezone
from typing import List
from schemas import SessionState, AnswerSubmission
from services.assessment_service import get_assessment_service
from services.skill_gap_engine import get_skill_gap_engine

class AssessmentAgent:
    def __init__(self):
        self.assessment_service = get_assessment_service()
        self.skill_gap_engine = get_skill_gap_engine()

    def start_assessment(self, session_state: SessionState) -> SessionState:
        if not session_state.selected_career:
            raise ValueError("No career selected in session. Please select a career first.")

        assessment_data = self.assessment_service.create_assessment_for_career(
            session_state.selected_career.id
        )
        session_state.assessment = assessment_data

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "AssessmentAgent",
            "action": "start_assessment",
            "details": {
                "assessment_id": assessment_data["assessment_id"],
                "total_questions": assessment_data["total_questions"]
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

    def evaluate_assessment(self, session_state: SessionState, answers: List[AnswerSubmission]) -> SessionState:
        if not session_state.assessment:
            raise ValueError("No active assessment found in session.")
        if not session_state.selected_career:
            raise ValueError("No selected career found in session.")

        assessment_id = session_state.assessment["assessment_id"]
        
        # Evaluate deterministic score
        result = self.assessment_service.evaluate_assessment(
            assessment_id=assessment_id,
            answers=answers,
            full_assessment_data=session_state.assessment,
            career=session_state.selected_career
        )
        session_state.assessment_result = result
        session_state.learner_profile.assessment_completed = True

        # Compute skill gaps
        gaps_response = self.skill_gap_engine.compute_skill_gaps(
            career=session_state.selected_career,
            assessment_result=result,
            profile_skills_0_5=session_state.learner_profile.current_skills
        )
        session_state.skill_gaps = gaps_response.skill_gaps

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "AssessmentAgent",
            "action": "evaluate_assessment",
            "details": {
                "assessment_id": assessment_id,
                "overall_score": result.overall_score,
                "readiness": result.readiness,
                "strengths_count": len(result.strengths),
                "weaknesses_count": len(result.weaknesses)
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

_assessment_agent_instance = None

def get_assessment_agent() -> AssessmentAgent:
    global _assessment_agent_instance
    if _assessment_agent_instance is None:
        _assessment_agent_instance = AssessmentAgent()
    return _assessment_agent_instance
