from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# 1. Skill Models
class Skill(BaseModel):
    id: str
    name: str
    category: str
    description: str
    prerequisites: List[str] = Field(default_factory=list)

# 2. Career Models
class Career(BaseModel):
    id: str
    name: str
    description: str
    required_skills: List[str]
    skill_weights: Dict[str, float]
    recommended_skill_order: List[str] = Field(default_factory=list)

# 3. Assessment Models
class AssessmentQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: Optional[str] = None
    skill_id: str
    difficulty: str = "intermediate"
    explanation: Optional[str] = None

class AssessmentQuestionPublic(BaseModel):
    id: str
    question: str
    options: List[str]
    skill_id: str
    difficulty: str

class AssessmentStartRequest(BaseModel):
    career_id: Optional[str] = None

class AssessmentStartResponse(BaseModel):
    assessment_id: str
    career_id: str
    career_name: str
    questions: List[AssessmentQuestionPublic]
    total_questions: int

class AnswerSubmission(BaseModel):
    question_id: str
    answer: str

class AssessmentSubmitRequest(BaseModel):
    assessment_id: str
    answers: List[AnswerSubmission]

class SkillScore(BaseModel):
    skill_id: str
    skill_name: str
    score: float
    category: str  # "weak", "developing", "strong", "proficient"
    correct_count: int
    total_count: int

class AssessmentResultResponse(BaseModel):
    assessment_id: str
    overall_score: float
    readiness: str  # "Novice", "Developing", "Proficient", "Expert"
    strengths: List[str] = Field(default_factory=list)
    developing: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    skill_scores: Dict[str, SkillScore] = Field(default_factory=dict)

# 4. Skill Gap Models
class SkillGap(BaseModel):
    skill_id: str
    skill_name: str
    current_score: float  # 0-100 scale from assessment or converted 0-5 scale
    target_score: float = 100.0
    gap: float
    category: str

class SkillGapsResponse(BaseModel):
    career_id: str
    career_name: str
    overall_score: float
    readiness: str
    skill_gaps: List[SkillGap]

# 5. Learner Profile
class LearnerProfile(BaseModel):
    learner_id: str
    goals: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    current_skills: Dict[str, float] = Field(default_factory=dict)  # 0 - 5 scale
    skill_level: str = "Beginner"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    selected_career: Optional[str] = None
    career_target: Optional[str] = None
    assessment_completed: bool = False

# 6. Learning Path & Milestone Models (Stairs-ready)
class Milestone(BaseModel):
    order: int
    course_id: str
    title: str
    description: str
    skill_focus: List[str]
    difficulty: str
    estimated_hours: int
    level: int  # Stair level position (1, 2, 3...)
    status: str = "available"  # "available", "locked", "completed"
    reasoning: str

class LearningPathResponse(BaseModel):
    learner_id: str
    career_id: str
    career_name: str
    overall_readiness: str
    learning_path: List[Milestone]

# 7. Trace & Session Models
class AgentTrace(BaseModel):
    timestamp: str
    agent_name: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)

class SessionState(BaseModel):
    session_id: str
    learner_id: str
    selected_career: Optional[Career] = None
    assessment: Optional[Dict[str, Any]] = None
    assessment_result: Optional[AssessmentResultResponse] = None
    skill_gaps: Optional[List[SkillGap]] = None
    learner_profile: LearnerProfile
    candidate_courses: List[Dict[str, Any]] = Field(default_factory=list)
    learning_path: List[Milestone] = Field(default_factory=list)
    feedback_log: List[Dict[str, Any]] = Field(default_factory=list)
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)

# 8. Communication Models
class SelectCareerRequest(BaseModel):
    career_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)

class FeedbackRequest(BaseModel):
    milestone_order: int
    rating: int  # 1-5 rating
    feedback_text: Optional[str] = None
