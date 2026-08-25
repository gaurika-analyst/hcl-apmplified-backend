from datetime import datetime, timezone
from typing import List, Optional
from schemas import SessionState, AnswerSubmission, LearningPathResponse
from agents.profile_agent import get_profile_agent
from agents.assessment_agent import get_assessment_agent
from agents.recommendation_agent import get_recommendation_agent
from agents.path_agent import get_path_agent
from agents.explainer_agent import get_explainer_agent
from agents.feedback_agent import get_feedback_agent

class Orchestrator:
    """
    Central Orchestrator.
    Sequences specialist agents based on session state workflow rules.
    Agents never invoke each other directly.
    """
    def __init__(self):
        self.profile_agent = get_profile_agent()
        self.assessment_agent = get_assessment_agent()
        self.recommendation_agent = get_recommendation_agent()
        self.path_agent = get_path_agent()
        self.explainer_agent = get_explainer_agent()
        self.feedback_agent = get_feedback_agent()

    def handle_select_career(self, session_state: SessionState, career_id: str) -> SessionState:
        # Step 1: Sequence ProfileAgent
        session_state = self.profile_agent.set_selected_career(session_state, career_id)
        
        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "Orchestrator",
            "action": "sequence_career_selection",
            "details": {"selected_career_id": career_id}
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

    def handle_start_assessment(self, session_state: SessionState) -> SessionState:
        # Step 1: Sequence AssessmentAgent
        session_state = self.assessment_agent.start_assessment(session_state)

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "Orchestrator",
            "action": "sequence_assessment_start",
            "details": {"assessment_id": session_state.assessment["assessment_id"]}
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

    def handle_submit_assessment(self, session_state: SessionState, answers: List[AnswerSubmission]) -> SessionState:
        # Step 1: Sequence AssessmentAgent (Evaluate & calculate skill gaps)
        session_state = self.assessment_agent.evaluate_assessment(session_state, answers)

        # Step 2: Sequence RecommendationAgent (Find matching courses)
        session_state = self.recommendation_agent.recommend(session_state)

        # Step 3: Sequence PathAgent (Build stairs-ready path)
        session_state = self.path_agent.generate_path(session_state)

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "Orchestrator",
            "action": "sequence_assessment_submission_and_path_generation",
            "details": {
                "overall_score": session_state.assessment_result.overall_score if session_state.assessment_result else 0,
                "milestone_count": len(session_state.learning_path)
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

    def handle_get_path(self, session_state: SessionState) -> SessionState:
        # Check if path needs generation/updating
        if not session_state.learning_path:
            if session_state.selected_career and session_state.skill_gaps:
                if not session_state.candidate_courses:
                    session_state = self.recommendation_agent.recommend(session_state)
                session_state = self.path_agent.generate_path(session_state)

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "Orchestrator",
            "action": "sequence_get_path",
            "details": {"milestone_count": len(session_state.learning_path)}
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

    def handle_chat(self, session_state: SessionState, user_message: str) -> str:
        response = self.explainer_agent.answer_chat_query(session_state, user_message)

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "Orchestrator",
            "action": "sequence_chat",
            "details": {"user_message": user_message}
        }
        session_state.agent_trace.append(trace_entry)
        return response

    def handle_feedback(
        self,
        session_state: SessionState,
        milestone_order: int,
        rating: int,
        feedback_text: Optional[str] = None
    ) -> SessionState:
        session_state = self.feedback_agent.log_feedback(
            session_state, milestone_order, rating, feedback_text
        )

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "Orchestrator",
            "action": "sequence_feedback",
            "details": {"milestone_order": milestone_order, "rating": rating}
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

_orchestrator_instance = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance
