from datetime import datetime, timezone
from typing import Optional
from schemas import SessionState

class FeedbackAgent:
    def log_feedback(
        self,
        session_state: SessionState,
        milestone_order: int,
        rating: int,
        feedback_text: Optional[str] = None
    ) -> SessionState:
        feedback_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "milestone_order": milestone_order,
            "rating": rating,
            "feedback_text": feedback_text or ""
        }
        session_state.feedback_log.append(feedback_entry)

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "FeedbackAgent",
            "action": "log_feedback",
            "details": {
                "milestone_order": milestone_order,
                "rating": rating
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

_feedback_agent_instance = None

def get_feedback_agent() -> FeedbackAgent:
    global _feedback_agent_instance
    if _feedback_agent_instance is None:
        _feedback_agent_instance = FeedbackAgent()
    return _feedback_agent_instance
