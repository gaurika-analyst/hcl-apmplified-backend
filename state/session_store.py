import uuid
from typing import Dict, Optional
from schemas import SessionState, LearnerProfile

class SessionStore:
    """
    Thread-safe in-memory session store mapped to Firebase user UIDs (learner_id).
    """
    def __init__(self):
        self._sessions_by_id: Dict[str, SessionState] = {}
        self._sessions_by_learner: Dict[str, SessionState] = {}

    def get_or_create_session(self, learner_id: str) -> SessionState:
        """
        Retrieves existing active session for learner_id (Firebase UID)
        or creates a new session if none exists.
        """
        if learner_id in self._sessions_by_learner:
            return self._sessions_by_learner[learner_id]
        
        return self.create_session(learner_id=learner_id)

    def create_session(self, learner_id: Optional[str] = None) -> SessionState:
        actual_learner_id = learner_id or f"learner_{uuid.uuid4().hex[:8]}"
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        initial_profile = LearnerProfile(
            learner_id=actual_learner_id,
            goals=["Career Transition / Skill Enhancement"],
            interests=["Technology"],
            current_skills={},
            skill_level="Beginner",
            preferences={"learning_pace": "moderate", "format": "interactive"},
            selected_career=None,
            career_target=None,
            assessment_completed=False
        )

        session_state = SessionState(
            session_id=session_id,
            learner_id=actual_learner_id,
            selected_career=None,
            assessment=None,
            assessment_result=None,
            skill_gaps=None,
            learner_profile=initial_profile,
            candidate_courses=[],
            learning_path=[],
            feedback_log=[],
            agent_trace=[]
        )

        self._sessions_by_id[session_id] = session_state
        self._sessions_by_learner[actual_learner_id] = session_state
        return session_state

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions_by_id.get(session_id)

    def get_session_by_learner_id(self, learner_id: str) -> Optional[SessionState]:
        return self._sessions_by_learner.get(learner_id)

    def save_session(self, session_state: SessionState) -> SessionState:
        self._sessions_by_id[session_state.session_id] = session_state
        self._sessions_by_learner[session_state.learner_id] = session_state
        return session_state

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions_by_id:
            sess = self._sessions_by_id[session_id]
            if sess.learner_id in self._sessions_by_learner:
                del self._sessions_by_learner[sess.learner_id]
            del self._sessions_by_id[session_id]
            return True
        return False

# Global Singleton Store
_session_store_instance = SessionStore()

def get_session_store() -> SessionStore:
    return _session_store_instance
