from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config import settings
from auth.firebase import verify_firebase_token

bearer_scheme = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    uid: str
    email: Optional[str] = "dev@example.com"
    name: Optional[str] = "Dev Learner"

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> AuthenticatedUser:
    """
    FastAPI dependency to extract and verify authenticated user.
    Supports AUTH_MODE='development' for zero-hassle local dev/testing
    and AUTH_MODE='firebase' for production Firebase ID token verification.
    """
    if settings.AUTH_MODE == "development":
        if credentials and credentials.credentials:
            try:
                decoded = verify_firebase_token(credentials.credentials)
                return AuthenticatedUser(
                    uid=decoded.get("uid", "dev-user"),
                    email=decoded.get("email", "dev@example.com"),
                    name=decoded.get("name", "Dev Learner")
                )
            except Exception:
                # In development mode, fall back cleanly if token is test dummy
                pass
        
        # Default development test user
        return AuthenticatedUser(
            uid="dev-user",
            email="dev@example.com",
            name="Dev Learner"
        )

    # AUTH_MODE == "firebase"
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header with Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        decoded = verify_firebase_token(credentials.credentials)
        return AuthenticatedUser(
            uid=decoded["uid"],
            email=decoded.get("email"),
            name=decoded.get("name")
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Firebase ID token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def verify_session_ownership(session_learner_id: str, current_user: AuthenticatedUser):
    """
    Verifies that the authenticated user owns the requested session.
    Returns 403 Forbidden if user UIDs do not match.
    """
    if current_user.uid != session_learner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access or modify this user session."
        )
