import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth
from config import settings

logger = logging.getLogger("auth.firebase")

_firebase_app = None

def initialize_firebase() -> Optional[firebase_admin.App]:
    """
    Safely initializes Firebase Admin SDK using environment credentials.
    Ensures single initialization across application lifecycle.
    """
    global _firebase_app
    if firebase_admin._apps:
        _firebase_app = firebase_admin.get_app()
        return _firebase_app

    if settings.AUTH_MODE == "development":
        logger.info("AUTH_MODE is set to 'development'. Firebase Admin SDK initialization skipped.")
        return None

    # In firebase mode, attempt initialization with credentials
    if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_CLIENT_EMAIL and settings.FIREBASE_PRIVATE_KEY:
        cred_dict = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
        }
        try:
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully with service account credentials.")
            return _firebase_app
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK with service account: {e}")
            raise RuntimeError(f"Firebase initialization failed: {e}")
    else:
        # Fallback to default application credentials if available
        try:
            _firebase_app = firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized with default application credentials.")
            return _firebase_app
        except Exception as e:
            logger.warning(f"Could not initialize Firebase Admin SDK with default credentials: {e}")
            return None

def verify_firebase_token(id_token: str) -> dict:
    """
    Verifies a Firebase ID token using Firebase Admin SDK auth service.
    Returns decoded token dictionary containing uid, email, name, etc.
    """
    initialize_firebase()
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise ValueError(f"Invalid Firebase ID token: {str(e)}")
