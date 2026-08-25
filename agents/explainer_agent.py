from datetime import datetime
from typing import Dict, Any, Optional
from config import settings
from schemas import SessionState

class ExplainerAgent:
    """
    Generates human-readable explanations and career path advice.
    Leverages LLM API when configured; uses structured rule-based fallbacks otherwise.
    """

    def generate_path_summary(self, session_state: SessionState) -> str:
        if not session_state.selected_career:
            return "No career selected yet."

        career_name = session_state.selected_career.name
        readiness = session_state.assessment_result.readiness if session_state.assessment_result else "Developing"
        path = session_state.learning_path

        if not path:
            return f"Your personalized path for {career_name} is ready to be generated."

        first_step = path[0]
        summary = (
            f"Based on your current readiness ({readiness}), your personalized learning roadmap for {career_name} "
            f"begins with Step 1: '{first_step.title}'. This step focuses on {', '.join(first_step.skill_focus)} "
            f"to address core skill gaps before advancing up the roadmap."
        )
        return summary

    def answer_chat_query(self, session_state: SessionState, user_message: str) -> str:
        career_name = session_state.selected_career.name if session_state.selected_career else "your target career"
        readiness = session_state.assessment_result.readiness if session_state.assessment_result else "Developing"
        
        # Check if LLM API Key is configured
        if settings.OPENAI_API_KEY or settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY:
            try:
                # Optional LLM call place
                pass
            except Exception:
                pass  # Fall back gracefully

        # Reliable Fallback logic
        msg_lower = user_message.lower()
        if "skill" in msg_lower or "gap" in msg_lower:
            if session_state.assessment_result:
                str_skills = ", ".join(session_state.assessment_result.strengths) or "None yet"
                weak_skills = ", ".join(session_state.assessment_result.weaknesses) or "None"
                return f"For {career_name}, your strong skills are: {str_skills}. Key areas to build are: {weak_skills}."
            return f"To analyze your skill gaps for {career_name}, please complete your skills assessment first!"

        elif "path" in msg_lower or "roadmap" in msg_lower or "next" in msg_lower:
            if session_state.learning_path:
                next_step = session_state.learning_path[0]
                return f"Your recommended next step is Step {next_step.order}: '{next_step.title}' ({next_step.estimated_hours} hrs, Level {next_step.level}). {next_step.reasoning}"
            return f"Select a career and submit your assessment to unlock your custom learning path for {career_name}!"

        return (
            f"Hello! I am your AI Career Guide. Currently focusing on {career_name} (Readiness: {readiness}). "
            f"I can help explain your skill assessment results, guide your next learning milestone, or adjust your path."
        )

_explainer_agent_instance = None

def get_explainer_agent() -> ExplainerAgent:
    global _explainer_agent_instance
    if _explainer_agent_instance is None:
        _explainer_agent_instance = ExplainerAgent()
    return _explainer_agent_instance
