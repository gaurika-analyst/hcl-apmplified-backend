import json
import os
import uuid
from typing import List, Dict, Any, Optional
from config import settings
from schemas import (
    Career, AssessmentQuestion, AssessmentQuestionPublic,
    AnswerSubmission, SkillScore, AssessmentResultResponse
)
from services.career_service import get_career_service

class AssessmentService:
    def __init__(self, assessment_seed_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assessment_seed_path = assessment_seed_path or os.path.join(base_dir, "db", "assessment_seed.json")
        self._question_bank: List[AssessmentQuestion] = []
        self._load_questions()

    def _load_questions(self):
        if os.path.exists(self.assessment_seed_path):
            with open(self.assessment_seed_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._question_bank = [AssessmentQuestion(**item) for item in data]

    def create_assessment_for_career(self, career_id: str) -> Dict[str, Any]:
        career_service = get_career_service()
        career = career_service.get_career_by_id(career_id)
        if not career:
            raise ValueError(f"Career '{career_id}' not found")

        required_skill_ids = set(career.required_skills)
        selected_questions: List[AssessmentQuestion] = []

        # Find questions matching required skills
        for q in self._question_bank:
            if q.skill_id in required_skill_ids:
                selected_questions.append(q)

        # Fallback: if any required skill lacks questions, add default basic question for that skill
        covered_skills = {q.skill_id for q in selected_questions}
        missing_skills = required_skill_ids - covered_skills

        for skill_id in missing_skills:
            skill = career_service.get_skill_by_id(skill_id)
            skill_name = skill.name if skill else skill_id.upper()
            fallback_q = AssessmentQuestion(
                id=f"q_fallback_{skill_id}",
                question=f"Which core concept is central to effective working with {skill_name}?",
                options=[
                    f"Understanding {skill_name} fundamentals and best practices",
                    "Random guess without testing",
                    "Ignoring documentation",
                    "None of the above"
                ],
                correct_answer=f"Understanding {skill_name} fundamentals and best practices",
                skill_id=skill_id,
                difficulty="beginner",
                explanation=f"Core concepts of {skill_name} provide foundational mastery."
            )
            selected_questions.append(fallback_q)

        assessment_id = f"assess_{uuid.uuid4().hex[:10]}"
        public_questions = [
            AssessmentQuestionPublic(
                id=q.id,
                question=q.question,
                options=q.options,
                skill_id=q.skill_id,
                difficulty=q.difficulty
            )
            for q in selected_questions
        ]

        return {
            "assessment_id": assessment_id,
            "career_id": career.id,
            "career_name": career.name,
            "questions": [q.model_dump() for q in public_questions],
            "full_questions": [q.model_dump() for q in selected_questions],
            "total_questions": len(selected_questions)
        }

    def evaluate_assessment(
        self,
        assessment_id: str,
        answers: List[AnswerSubmission],
        full_assessment_data: Dict[str, Any],
        career: Career
    ) -> AssessmentResultResponse:
        career_service = get_career_service()
        full_questions_dict = {
            q["id"]: q for q in full_assessment_data.get("full_questions", [])
        }

        # Track results by skill_id
        skill_correct: Dict[str, int] = {}
        skill_total: Dict[str, int] = {}

        # Initialize tracking for all required career skills
        for skill_id in career.required_skills:
            skill_correct[skill_id] = 0
            skill_total[skill_id] = 0

        # Evaluate submitted answers
        submitted_dict = {ans.question_id: ans.answer for ans in answers}

        for q_id, q_data in full_questions_dict.items():
            skill_id = q_data["skill_id"]
            if skill_id not in skill_total:
                skill_total[skill_id] = 0
                skill_correct[skill_id] = 0

            skill_total[skill_id] += 1
            user_answer = submitted_dict.get(q_id)
            correct_answer = q_data.get("correct_answer")

            if user_answer and correct_answer and user_answer.strip().lower() == correct_answer.strip().lower():
                skill_correct[skill_id] += 1

        skill_scores: Dict[str, SkillScore] = {}
        strengths: List[str] = []
        developing: List[str] = []
        weaknesses: List[str] = []

        total_weighted_score = 0.0
        weights = career.skill_weights

        for skill_id in career.required_skills:
            tot = skill_total.get(skill_id, 0)
            corr = skill_correct.get(skill_id, 0)
            
            if tot > 0:
                score = round((corr / tot) * 100.0, 1)
            else:
                score = 50.0  # Default neutral score if no questions existed
            
            # Determine skill category based on configurable thresholds
            if score <= settings.WEAK_THRESHOLD:
                category = "weak"
            elif score <= settings.DEVELOPING_THRESHOLD:
                category = "developing"
            elif score <= settings.STRONG_THRESHOLD:
                category = "strong"
            else:
                category = "proficient"

            skill_obj = career_service.get_skill_by_id(skill_id)
            skill_name = skill_obj.name if skill_obj else skill_id.title()

            skill_scores[skill_id] = SkillScore(
                skill_id=skill_id,
                skill_name=skill_name,
                score=score,
                category=category,
                correct_count=corr,
                total_count=tot
            )

            # Categorize into lists
            if category in ("strong", "proficient"):
                strengths.append(skill_name)
            elif category == "developing":
                developing.append(skill_name)
            else:
                weaknesses.append(skill_name)

            # Add to weighted overall score
            w = weights.get(skill_id, 1.0 / len(career.required_skills))
            total_weighted_score += score * w

        overall_score = round(total_weighted_score, 1)

        # Readiness classification
        if overall_score >= 85.0:
            readiness = "Expert"
        elif overall_score >= 70.0:
            readiness = "Proficient"
        elif overall_score >= 40.0:
            readiness = "Developing"
        else:
            readiness = "Novice"

        return AssessmentResultResponse(
            assessment_id=assessment_id,
            overall_score=overall_score,
            readiness=readiness,
            strengths=strengths,
            developing=developing,
            weaknesses=weaknesses,
            skill_scores=skill_scores
        )

_assessment_service_instance = None

def get_assessment_service() -> AssessmentService:
    global _assessment_service_instance
    if _assessment_service_instance is None:
        _assessment_service_instance = AssessmentService()
    return _assessment_service_instance
