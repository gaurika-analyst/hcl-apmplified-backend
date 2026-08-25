from abc import ABC, abstractmethod
from typing import List, Dict, Any
from schemas import Career, SkillGap, LearnerProfile

class RecommendationEngine(ABC):
    """
    Abstract Base Class for candidate course recommendations.
    Enables future ML model integration (MLRecommendationEngine) without API breaking changes.
    """
    @abstractmethod
    def recommend_courses(
        self,
        career: Career,
        skill_gaps: List[SkillGap],
        learner_profile: LearnerProfile,
        available_courses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        pass


class RuleBasedRecommendationEngine(RecommendationEngine):
    """
    Deterministic rule-based recommendation engine.
    Matches candidate courses against identified skill gaps and prerequisite order.
    """
    def recommend_courses(
        self,
        career: Career,
        skill_gaps: List[SkillGap],
        learner_profile: LearnerProfile,
        available_courses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Map skill_id -> gap info
        gap_map = {g.skill_id: g for g in skill_gaps}
        
        # Priority 1: Weak skills (0-39 score, largest gap)
        # Priority 2: Developing skills (40-69 score)
        # Priority 3: Other skills required for target career
        
        scored_courses = []
        for course in available_courses:
            skills_covered = course.get("skills_covered", [])
            match_score = 0.0
            reasons = []

            for sk in skills_covered:
                if sk in gap_map:
                    gap_info = gap_map[sk]
                    if gap_info.category == "weak":
                        match_score += 10.0 + (gap_info.gap / 10.0)
                        reasons.append(f"Addresses critical weak skill '{gap_info.skill_name}' (Score: {gap_info.current_score}%)")
                    elif gap_info.category == "developing":
                        match_score += 5.0 + (gap_info.gap / 20.0)
                        reasons.append(f"Strengthens developing skill '{gap_info.skill_name}' (Score: {gap_info.current_score}%)")
                    elif gap_info.category == "strong":
                        match_score += 1.0
                        reasons.append(f"Reinforces strong skill '{gap_info.skill_name}'")
                elif sk in career.required_skills:
                    match_score += 2.0
                    reasons.append(f"Covers required skill '{sk}'")

            if match_score > 0:
                annotated_course = dict(course)
                annotated_course["recommendation_score"] = round(match_score, 2)
                annotated_course["recommendation_reasons"] = reasons
                scored_courses.append(annotated_course)

        # Sort candidate courses by recommendation score descending
        scored_courses.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return scored_courses


class MLRecommendationEngine(RecommendationEngine):
    """
    Placeholder for future ML recommendation engine integration.
    Will connect to trained ranking model / embedding retrieval service.
    """
    def recommend_courses(
        self,
        career: Career,
        skill_gaps: List[SkillGap],
        learner_profile: LearnerProfile,
        available_courses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Future ML implementation goes here
        raise NotImplementedError("ML recommendation model not initialized. Use RuleBasedRecommendationEngine.")

_recommendation_engine_instance = None

def get_recommendation_engine() -> RecommendationEngine:
    global _recommendation_engine_instance
    if _recommendation_engine_instance is None:
        _recommendation_engine_instance = RuleBasedRecommendationEngine()
    return _recommendation_engine_instance
