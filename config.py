import os
from typing import List

class Settings:
    PROJECT_NAME: str = "AI Personalized Career Recommendation & Learning Path API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""

    # Authentication Mode: "development" or "firebase"
    AUTH_MODE: str = os.getenv("AUTH_MODE", "development").lower()

    # Frontend URL & CORS origins
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    ALLOWED_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "ALLOWED_ORIGINS",
            f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')},http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
        ).split(",") if origin.strip()
    ]

    # Firebase Admin SDK Credentials
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")

    # Skill Score Thresholds (0 - 100)
    WEAK_THRESHOLD: float = float(os.getenv("WEAK_THRESHOLD", "39.0"))
    DEVELOPING_THRESHOLD: float = float(os.getenv("DEVELOPING_THRESHOLD", "69.0"))
    STRONG_THRESHOLD: float = float(os.getenv("STRONG_THRESHOLD", "84.0"))
    PROFICIENT_THRESHOLD: float = float(os.getenv("PROFICIENT_THRESHOLD", "100.0"))

    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

settings = Settings()
