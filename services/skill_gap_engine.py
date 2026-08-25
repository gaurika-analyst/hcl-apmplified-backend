from typing import List, Dict
from schemas import Career, AssessmentResultResponse, SkillGap, SkillGapsResponse
from services.career_service import get_career_service

class SkillGapEngine:
    def __init__(self):
        self.career_service = get_career_service()

    def compute_skill_gaps(
        self,
        career: Career,
        assessment_result: AssessmentResultResponse,
        profile_skills_0_5: Dict[str, float] = None
    ) -> SkillGapsResponse:
        profile_skills_0_5 = profile_skills_0_5 or {}
        gaps: List[SkillGap] = []

        for skill_id in career.required_skills:
            skill_obj = self.career_service.get_skill_by_id(skill_id)
            skill_name = skill_obj.name if skill_obj else skill_id.title()

            # Determine score (0-100 scale)
            if assessment_result and skill_id in assessment_result.skill_scores:
                current_score = assessment_result.skill_scores[skill_id].score
                category = assessment_result.skill_scores[skill_id].category
            elif skill_id in profile_skills_0_5:
                # Convert 0-5 scale to 0-100 scale
                val_0_5 = profile_skills_0_5[skill_id]
                current_score = round((val_0_5 / 5.0) * 100.0, 1)
                if current_score <= 39:
                    category = "weak"
                elif current_score <= 69:
                    category = "developing"
                elif current_score <= 84:
                    category = "strong"
                else:
                    category = "proficient"
            else:
                current_score = 0.0
                category = "weak"

            target_score = 100.0
            gap_amount = round(max(0.0, target_score - current_score), 1)

            gaps.append(
                SkillGap(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    current_score=current_score,
                    target_score=target_score,
                    gap=gap_amount,
                    category=category
                )
            )

        # Sort gaps: weak skills first, then largest gap amount
        gaps.sort(key=lambda g: (0 if g.category == "weak" else (1 if g.category == "developing" else 2), -g.gap))

        overall_score = assessment_result.overall_score if assessment_result else 0.0
        readiness = assessment_result.readiness if assessment_result else "Novice"

        return SkillGapsResponse(
            career_id=career.id,
            career_name=career.name,
            overall_score=overall_score,
            readiness=readiness,
            skill_gaps=gaps
        )

_skill_gap_engine_instance = None

def get_skill_gap_engine() -> SkillGapEngine:
    global _skill_gap_engine_instance
    if _skill_gap_engine_instance is None:
        _skill_gap_engine_instance = SkillGapEngine()
    return _skill_gap_engine_instance
