from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.auth.exceptions import InvalidToken
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.service import AuthService
from src.database import get_session

_bearer = HTTPBearer()


def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(UserRepository(session))


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
) -> User:
    """Use as a dependency on any route that needs a signed-in user."""
    try:
        return service.user_from_token(creds.credentials)
    except InvalidToken as e:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}) from e
