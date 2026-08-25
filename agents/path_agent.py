from datetime import datetime, timezone
from typing import List, Dict, Any, Set
from schemas import SessionState, Milestone, SkillGap
from services.career_service import get_career_service

class PathAgent:
    def __init__(self):
        self.career_service = get_career_service()

    def generate_path(self, session_state: SessionState) -> SessionState:
        if not session_state.selected_career:
            raise ValueError("No career selected.")
        if not session_state.candidate_courses:
            raise ValueError("No candidate courses available for path generation.")

        career = session_state.selected_career
        candidate_courses = session_state.candidate_courses
        
        # Build map of skill scores (0-100)
        skill_score_map: Dict[str, float] = {}
        if session_state.assessment_result:
            for sid, sc in session_state.assessment_result.skill_scores.items():
                skill_score_map[sid] = sc.score
        elif session_state.skill_gaps:
            for sg in session_state.skill_gaps:
                skill_score_map[sg.skill_id] = sg.current_score

        # Identify which skills the learner has already mastered (>= 75.0 score)
        mastered_skills: Set[str] = {
            sid for sid, score in skill_score_map.items() if score >= 75.0
        }

        # Filter candidates: exclude courses covering ONLY mastered skills, unless no other courses remain
        courses_to_plan = []
        for course in candidate_courses:
            skills_covered = set(course.get("skills_covered", []))
            unmastered = skills_covered - mastered_skills
            if unmastered:
                courses_to_plan.append(course)
        
        if not courses_to_plan:
            # If learner is already strong in everything, retain top candidate courses
            courses_to_plan = candidate_courses[:3]

        # Order courses by level and prerequisites
        # Sort key: course level, difficulty level priority, number of unmastered skills covered
        def sort_key(c):
            level = c.get("level", 1)
            diff_rank = {"beginner": 1, "intermediate": 2, "advanced": 3}.get(c.get("difficulty", "beginner"), 1)
            return (level, diff_rank)

        ordered_candidates = sorted(courses_to_plan, key=sort_key)

        # Assemble stairs-ready milestones
        milestones: List[Milestone] = []
        satisfied_prereq_courses: Set[str] = set()

        for idx, course in enumerate(ordered_candidates, start=1):
            course_id = course["id"]
            prereqs = course.get("prerequisites", [])
            skills_covered = course.get("skills_covered", [])
            level = course.get("level", idx)

            # Determine initial status
            # If all course prerequisites are satisfied or satisfied by mastered skills, status is 'available', else 'locked'
            all_prereqs_met = True
            for prereq in prereqs:
                if prereq not in satisfied_prereq_courses:
                    # Check if prerequisite course skills are already mastered
                    prereq_course_obj = next((c for c in candidate_courses if c["id"] == prereq), None)
                    if prereq_course_obj:
                        prereq_skills = set(prereq_course_obj.get("skills_covered", []))
                        if not prereq_skills.issubset(mastered_skills):
                            all_prereqs_met = False
                            break

            # The first milestone in the path is always available to start
            if idx == 1:
                status = "available"
            else:
                status = "available" if all_prereqs_met else "locked"

            # Formulate structured reasoning
            reasons = course.get("recommendation_reasons", [])
            if reasons:
                reasoning = "; ".join(reasons)
            else:
                skills_str = ", ".join([self.career_service.get_skill_by_id(s).name if self.career_service.get_skill_by_id(s) else s for s in skills_covered])
                reasoning = f"Focuses on developing essential skills: {skills_str} for {career.name}."

            milestone = Milestone(
                order=idx,
                course_id=course_id,
                title=course.get("title", course_id.title()),
                description=course.get("description", ""),
                skill_focus=skills_covered,
                difficulty=course.get("difficulty", "beginner"),
                estimated_hours=course.get("estimated_hours", 10),
                level=level,
                status=status,
                reasoning=reasoning
            )
            milestones.append(milestone)
            satisfied_prereq_courses.add(course_id)

        session_state.learning_path = milestones

        trace_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "PathAgent",
            "action": "generate_learning_path",
            "details": {
                "milestones_count": len(milestones),
                "starting_step": milestones[0].title if milestones else None,
                "mastered_skills": list(mastered_skills)
            }
        }
        session_state.agent_trace.append(trace_entry)
        return session_state

_path_agent_instance = None

def get_path_agent() -> PathAgent:
    global _path_agent_instance
    if _path_agent_instance is None:
        _path_agent_instance = PathAgent()
    return _path_agent_instance
