import json
import os
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    In-memory vector store abstraction for candidate course retrieval.
    Offers fallback keyword/skill matching when external embeddings/LLMs are unavailable.
    """
    def __init__(self, course_seed_path: Optional[str] = None):
        if course_seed_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            course_seed_path = os.path.join(base_dir, "course_seed.json")
        self.course_seed_path = course_seed_path
        self.courses: List[Dict[str, Any]] = self._load_courses()

    def _load_courses(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.course_seed_path):
            with open(self.course_seed_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def get_all_courses(self) -> List[Dict[str, Any]]:
        return self.courses

    def search_by_skills(self, target_skill_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves courses covering any of the target skill IDs,
        ordered by how many target skills are covered.
        """
        results = []
        target_set = set(target_skill_ids)
        for course in self.courses:
            course_skills = set(course.get("skills_covered", []))
            overlap = course_skills.intersection(target_set)
            if overlap:
                score = len(overlap)
                results.append((score, course))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in results]

    def search_by_query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        scored_courses = []
        for course in self.courses:
            score = 0
            title = course.get("title", "").lower()
            desc = course.get("description", "").lower()
            skills = [s.lower() for s in course.get("skills_covered", [])]
            
            if query_lower in title:
                score += 3
            if query_lower in desc:
                score += 1
            for sk in skills:
                if query_lower in sk:
                    score += 2
                    
            if score > 0:
                scored_courses.append((score, course))
                
        scored_courses.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_courses[:limit]]

_vector_store_instance = None

def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
