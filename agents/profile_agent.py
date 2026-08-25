from datetime import datetime, timezone
from schemas import SessionState, Career
from services.career_service import get_career_service

class ProfileAgent:
    def __init__(self):
        self.career_service = get_career_service()

    def set_selected_career(self, session_state: SessionState, career_id: str) -> SessionState:
        career = self.career_service.get_career_by_id(career_id)
        if not career:
            raise ValueError(f"Invalid career_id: {career_id}")

        session_state.selected_career = career
        session_state.learner_profile.selected_career = career.id
        session_state.learner_profile.career_target = career.name

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "ProfileAgent",
            "action": "set_selected_career",
            "details": {
                "career_id": career.id,
                "career_name": career.name,
                "required_skills": career.required_skills
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

_profile_agent_instance = None

def get_profile_agent() -> ProfileAgent:
    global _profile_agent_instance
    if _profile_agent_instance is None:
        _profile_agent_instance = ProfileAgent()
    return _profile_agent_instance
