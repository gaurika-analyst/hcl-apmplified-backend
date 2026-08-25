import json
import os
from typing import List, Dict, Optional
from schemas import Career, Skill

class CareerService:
    def __init__(self, career_seed_path: Optional[str] = None, skill_seed_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.career_seed_path = career_seed_path or os.path.join(base_dir, "db", "career_seed.json")
        self.skill_seed_path = skill_seed_path or os.path.join(base_dir, "db", "skill_seed.json")
        
        self._careers_cache: Dict[str, Career] = {}
        self._skills_cache: Dict[str, Skill] = {}
        self._reload_data()

    def _reload_data(self):
        if os.path.exists(self.skill_seed_path):
            with open(self.skill_seed_path, "r", encoding="utf-8") as f:
                skills_data = json.load(f)
                for item in skills_data:
                    skill = Skill(**item)
                    self._skills_cache[skill.id] = skill

        if os.path.exists(self.career_seed_path):
            with open(self.career_seed_path, "r", encoding="utf-8") as f:
                careers_data = json.load(f)
                for item in careers_data:
                    career = Career(**item)
                    self._careers_cache[career.id] = career

    def get_all_careers(self) -> List[Career]:
        return list(self._careers_cache.values())

    def get_career_by_id(self, career_id: str) -> Optional[Career]:
        return self._careers_cache.get(career_id)

    def get_all_skills(self) -> List[Skill]:
        return list(self._skills_cache.values())

    def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        return self._skills_cache.get(skill_id)

    def get_career_skills(self, career_id: str) -> List[Skill]:
        career = self.get_career_by_id(career_id)
        if not career:
            return []
        return [self._skills_cache[sid] for sid in career.required_skills if sid in self._skills_cache]

    def get_career_skill_weights(self, career_id: str) -> Dict[str, float]:
        career = self.get_career_by_id(career_id)
        if not career:
            return {}
        return career.skill_weights

_career_service_instance = None

def get_career_service() -> CareerService:
    global _career_service_instance
    if _career_service_instance is None:
        _career_service_instance = CareerService()
    return _career_service_instance
