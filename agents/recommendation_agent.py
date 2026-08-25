from datetime import datetime, timezone
from schemas import SessionState
from db.vector_store import get_vector_store
from services.recommendation_engine import get_recommendation_engine

class RecommendationAgent:
    def __init__(self):
        self.vector_store = get_vector_store()
        self.recommendation_engine = get_recommendation_engine()

    def recommend(self, session_state: SessionState) -> SessionState:
        if not session_state.selected_career:
            raise ValueError("No career selected.")
        if not session_state.skill_gaps:
            raise ValueError("No skill gaps computed. Run assessment evaluation first.")

        all_courses = self.vector_store.get_all_courses()
        
        recommended_courses = self.recommendation_engine.recommend_courses(
            career=session_state.selected_career,
            skill_gaps=session_state.skill_gaps,
            learner_profile=session_state.learner_profile,
            available_courses=all_courses
        )

        session_state.candidate_courses = recommended_courses

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "RecommendationAgent",
            "action": "recommend_candidate_courses",
            "details": {
                "candidate_count": len(recommended_courses),
                "top_course": recommended_courses[0]["id"] if recommended_courses else None
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

_recommendation_agent_instance = None

def get_recommendation_agent() -> RecommendationAgent:
    global _recommendation_agent_instance
    if _recommendation_agent_instance is None:
        _recommendation_agent_instance = RecommendationAgent()
    return _recommendation_agent_instance
